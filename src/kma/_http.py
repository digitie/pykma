"""HTTP client helpers backed by httpx."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, NoReturn
from xml.etree import ElementTree

import httpx

from .exceptions import KmaAuthError, KmaRequestError, KmaServerError
from .metadata import redact_credentials_in_text

RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

#: httpx.RequestError subtypes worth retrying — transient connection/timeout
#: conditions. Non-transient errors (e.g. httpx.UnsupportedProtocol,
#: httpx.InvalidURL) are deliberately excluded so a permanently broken client
#: configuration fails on the first attempt instead of burning the retry budget.
TRANSIENT_REQUEST_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)

#: data.go.kr 표준 result code ``03``(NODATA_ERROR) — 조회 결과 없음.
#: 인증/서버 오류와 달리 정상적인 빈 결과이므로 예외 대신 빈 body로 정규화한다.
NO_DATA_RESULT_CODE = "03"


def empty_kma_body(body: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """data.go.kr NO_DATA(``03``) 응답을 빈 결과 body로 정규화합니다.

    item 추출(`body.items.item`)이 빈 list가 되고 pagination metadata가
    ``totalCount == 0``으로 해석되도록 강제해, 호출자가 빈 page/list를
    그대로 받게 합니다. 원본 ``body``의 다른 키(``pageNo`` 등)는 보존합니다.
    """

    normalized: dict[str, Any] = dict(body) if body is not None else {}
    normalized["items"] = {"item": []}
    normalized["totalCount"] = 0
    return normalized


def _backoff_with_jitter(backoff_factor: float, attempt: int) -> float:
    """Exponential backoff with equal jitter to avoid a thundering herd.

    Returns a sleep duration in ``[base / 2, base]`` where
    ``base = backoff_factor * 2 ** attempt``. Spreading retries randomly across
    that band keeps many clients that failed at the same instant from retrying
    in lockstep, while preserving the overall exponential growth.
    """

    base = backoff_factor * (2**attempt)
    half = base / 2
    return float(half + random.uniform(0, half))


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Parse a ``Retry-After`` header (delay-seconds or HTTP-date) into seconds.

    Returns ``None`` if the header is absent or unparseable.
    """

    value = response.headers.get("Retry-After")
    if value is None:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        retry_date = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if retry_date.tzinfo is None:
        retry_date = retry_date.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_date - datetime.now(timezone.utc)).total_seconds())


def raise_for_kma_result_code(
    code: str,
    message: str,
    *,
    provider: str,
    endpoint: str,
    label: str,
) -> None:
    """Map a non-``00`` data.go.kr/KMA ``resultCode`` to a ``kma`` exception.

    Shared by every client so the result-code → exception policy lives in one
    place. ``label`` is the human-facing prefix in the message (e.g. ``"KMA"``,
    ``"data.go.kr"``) while ``provider`` is the machine value stored on the
    exception. ``message`` is redacted before it reaches the exception text.

    ``03``(NO_DATA)은 정상적인 빈 결과이므로 호출자가 이 함수에 도달하기
    전에 :func:`empty_kma_body`로 정규화해야 합니다 (unwrap 단계에서 처리).
    """

    text = f"{label} API returned {code}: {redact_credentials_in_text(message)}"
    if code in {"20", "21", "30", "31", "32", "33"}:
        raise KmaAuthError(
            text,
            provider=provider,
            endpoint=endpoint,
            result_code=code,
            failure_kind="auth",
            retryable=False,
        )
    if code in {"04", "99"}:
        raise KmaServerError(
            text,
            provider=provider,
            endpoint=endpoint,
            result_code=code,
            failure_kind="server",
            retryable=True,
        )
    if code == "22":
        # 일일 요청 한도 초과. 한도는 **자정에 리셋**되므로 같은 날 재시도는 몇 번을
        # 해도 같은 코드를 받는다. 이 축(`retryable`)은 위 분기들이 정한 대로
        # "즉시 재시도가 성공할 만한가"이지 "언젠가 성공할 수 있는가"가 아니다 —
        # auth(20/30/31)가 False이고 server(04/99)가 True인 것이 그 기준이다.
        # True로 두면 호출자가 성공할 수 없는 것에 retry budget을 태운다.
        raise KmaRequestError(
            text,
            provider=provider,
            endpoint=endpoint,
            result_code=code,
            failure_kind="quota",
            retryable=False,
        )
    raise KmaRequestError(
        text,
        provider=provider,
        endpoint=endpoint,
        result_code=code,
        failure_kind="request",
        retryable=False,
    )


def raise_for_kma_xml_error_body(
    text: str,
    *,
    provider: str,
    endpoint: str,
    label: str,
) -> bool:
    """HTTP 200의 data.go.kr XML 오류 envelope를 분류합니다.

    JSON을 요청해도 gateway-level 오류는 ``OpenAPI_ServiceResponse`` XML로
    반환될 수 있습니다. XML이 아니거나 인식 가능한 오류 코드가 없으면 호출자가
    원래 parse error를 내도록 ``False``를 반환합니다. ``03``(NO_DATA)은 JSON
    envelope와 같은 빈 성공 계약을 위해 ``True``를 반환하고, 나머지 오류는 typed
    예외를 올립니다.
    """

    # HTTP decoder가 BOM을 보존해도 오류 envelope 판별이 무음으로 빠지지 않는다.
    stripped = text.lstrip("\ufeff \t\r\n")
    if not stripped.startswith("<"):
        return False
    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError:
        return False

    def _local_name(tag: object) -> str:
        return str(tag).rsplit("}", 1)[-1]

    if _local_name(root.tag) != "OpenAPI_ServiceResponse":
        return False
    header = next(
        (child for child in root if _local_name(child.tag) == "cmmMsgHeader"),
        None,
    )
    if header is None:
        return False

    values: dict[str, str] = {}
    for element in header.iter():
        tag = _local_name(element.tag)
        if element.text is not None and tag not in values:
            values[tag] = element.text.strip()
    code = values.get("returnReasonCode") or values.get("resultCode")
    if not code or code == "00":
        return False
    if code == NO_DATA_RESULT_CODE:
        return True
    message = (
        values.get("returnAuthMsg")
        or values.get("resultMsg")
        or values.get("errMsg")
        or "XML error response"
    )
    raise_for_kma_result_code(
        code,
        message,
        provider=provider,
        endpoint=endpoint,
        label=label,
    )
    return False  # pragma: no cover - raise_for_kma_result_code는 항상 예외를 올린다.


def raise_for_kma_http_error(
    exc: httpx.HTTPStatusError,
    *,
    provider: str,
    endpoint: str,
    label: str,
    detail: str = "",
) -> NoReturn:
    """Map an httpx ``HTTPStatusError`` to the matching ``kma`` exception.

    Shared by every client so the HTTP status → exception policy lives in one
    place. ``label`` is the human-facing prefix in the message (e.g. ``"KMA"``,
    ``"data.go.kr"``, ``"APIHub"``) while ``provider`` is the machine value
    stored on the exception. ``detail`` appends an optional ``": <detail>"``
    suffix extracted from the response body.
    """

    status = exc.response.status_code if exc.response is not None else None
    suffix = f": {detail}" if detail else ""
    if status and status >= 500:
        raise KmaServerError(
            f"{label} server returned HTTP {status}{suffix}",
            provider=provider,
            endpoint=endpoint,
            status_code=status,
            failure_kind="server",
            retryable=True,
        ) from None
    if status in {401, 403}:
        raise KmaAuthError(
            f"{label} request failed with HTTP {status}{suffix}",
            provider=provider,
            endpoint=endpoint,
            status_code=status,
            failure_kind="auth",
            retryable=False,
        ) from None
    if status == 429:
        raise KmaRequestError(
            f"{label} request failed with HTTP {status}{suffix}",
            provider=provider,
            endpoint=endpoint,
            status_code=status,
            failure_kind="rate_limit",
            retryable=True,
        ) from None
    raise KmaRequestError(
        f"{label} request failed with HTTP {status}{suffix}",
        provider=provider,
        endpoint=endpoint,
        status_code=status,
        failure_kind="request",
        retryable=False,
    ) from None


def raise_for_kma_network_error(
    *,
    provider: str,
    endpoint: str,
    label: str,
) -> NoReturn:
    """Map an httpx ``RequestError`` (connection/timeout) to ``KmaRequestError``."""

    raise KmaRequestError(
        f"{label} request failed",
        provider=provider,
        endpoint=endpoint,
        failure_kind="network",
        retryable=True,
    ) from None


def build_client() -> httpx.Client:
    """Create the default synchronous httpx client."""

    return httpx.Client(follow_redirects=True)


def build_async_client() -> httpx.AsyncClient:
    """Create the default asynchronous httpx client."""

    return httpx.AsyncClient(follow_redirects=True)


def build_session(retries: int = 3) -> httpx.Client:
    """Backward-compatible alias for older code that asked for a session."""

    _ = retries
    return build_client()


def get_with_retries(
    client: Any,
    url: str,
    *,
    params: dict[str, Any] | None,
    timeout: float,
    retries: int,
    backoff_factor: float = 0.3,
) -> Any:
    """GET a URL with retry behavior matching the old requests adapter."""

    attempts = max(1, retries + 1)
    last_exc: httpx.HTTPError | None = None
    for attempt in range(attempts):
        retry_after: float | None = None
        try:
            response = client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if not _should_retry_status(exc) or attempt >= attempts - 1:
                raise
            last_exc = exc
            if exc.response.status_code == 429:
                retry_after = _retry_after_seconds(exc.response)
        except TRANSIENT_REQUEST_ERRORS as exc:
            if attempt >= attempts - 1:
                raise
            last_exc = exc
        sleep_seconds = _backoff_with_jitter(backoff_factor, attempt)
        if retry_after is not None:
            sleep_seconds = max(sleep_seconds, retry_after)
        time.sleep(sleep_seconds)
    if last_exc is not None:  # pragma: no cover - defensive fallback
        raise last_exc
    raise RuntimeError("HTTP request failed before it could be attempted")


async def async_get_with_retries(
    client: Any,
    url: str,
    *,
    params: dict[str, Any] | None,
    timeout: float,
    retries: int,
    backoff_factor: float = 0.3,
) -> Any:
    """Async GET a URL with retry behavior matching the sync helper."""

    attempts = max(1, retries + 1)
    last_exc: httpx.HTTPError | None = None
    for attempt in range(attempts):
        retry_after: float | None = None
        try:
            response = await client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if not _should_retry_status(exc) or attempt >= attempts - 1:
                raise
            last_exc = exc
            if exc.response.status_code == 429:
                retry_after = _retry_after_seconds(exc.response)
        except TRANSIENT_REQUEST_ERRORS as exc:
            if attempt >= attempts - 1:
                raise
            last_exc = exc
        sleep_seconds = _backoff_with_jitter(backoff_factor, attempt)
        if retry_after is not None:
            sleep_seconds = max(sleep_seconds, retry_after)
        await asyncio.sleep(sleep_seconds)
    if last_exc is not None:  # pragma: no cover - defensive fallback
        raise last_exc
    raise RuntimeError("HTTP request failed before it could be attempted")


def _should_retry_status(exc: httpx.HTTPStatusError) -> bool:
    return exc.response.status_code in RETRY_STATUS_CODES

"""기상청 APIHub 범용 클라이언트와 탐색 도우미."""

from __future__ import annotations

import csv
import html
import io
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus, unquote_plus, urlsplit, urlunsplit

import httpx

from ._credentials import APIHUB_ENV_NAMES, first_env_value, normalize_api_key
from ._http import async_get_with_retries, build_async_client, build_session, get_with_retries
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .metadata import (
    ResponseMetadata,
    is_credential_param,
    make_response_metadata,
    redact_credentials_in_text,
    request_params_from_url,
)

APIHUB_BASE_URL = "https://apihub.kma.go.kr"
APIHUB_CATEGORY_IDS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15)

APIHUB_CATEGORIES: dict[int, str] = {
    2: "지상관측",
    3: "해양관측",
    4: "고층관측",
    5: "레이더",
    6: "위성",
    7: "지진/화산",
    8: "태풍",
    9: "수치모델",
    10: "예특보",
    11: "응용기상",
    12: "세계기상",
    13: "산업특화",
    14: "항공기상",
    15: "기후변화",
}


@dataclass(frozen=True)
class ApiHubService:
    category_id: int
    category_name: str
    service_id: int
    service_name: str


@dataclass(frozen=True)
class ApiHubEndpoint:
    path: str
    parameters: tuple[str, ...]
    sample_params: Mapping[str, str]
    query_parts: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ApiHubEndpointSpec:
    name: str
    title: str
    category_id: int
    category_name: str
    service_id: int
    service_name: str
    path: str
    parameters: tuple[str, ...]
    sample_params: Mapping[str, str]
    query_parts: tuple[tuple[str, str], ...]
    response_kind: str
    source: str


@dataclass(frozen=True)
class ApiHubAttachment:
    title: str
    url: str
    filename: str
    category_id: int
    category_name: str
    service_id: int
    service_name: str
    kind: str


@dataclass(frozen=True)
class ApiHubTextTable:
    headers: tuple[str, ...]
    rows: tuple[Mapping[str, str], ...]
    comments: tuple[str, ...]
    raw_lines: tuple[str, ...]


@dataclass(frozen=True)
class ApiHubImage:
    content: bytes
    content_type: str
    format: str | None
    width: int | None
    height: int | None


@dataclass(frozen=True)
class ApiHubResponse:
    url: str
    status_code: int
    content_type: str
    text: str
    content: bytes
    metadata: ResponseMetadata | None = None

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except ValueError as exc:
            raise KmaParseError(
                "APIHub response was not JSON",
                provider=self.metadata.provider if self.metadata else "apihub",
                endpoint=self.metadata.endpoint if self.metadata else None,
                status_code=self.status_code,
                failure_kind="parse",
                retryable=False,
            ) from exc

    def text_table(self, delimiter: str | None = None) -> ApiHubTextTable:
        return parse_apihub_text_table(self.text, delimiter=delimiter)

    def image(self) -> ApiHubImage:
        image_format, width, height = detect_image_info(self.content)
        return ApiHubImage(
            content=self.content,
            content_type=self.content_type,
            format=image_format,
            width=width,
            height=height,
        )


class ApiHubClient:
    """기상청 APIHub `authKey` API용 범용 클라이언트.

    APIHub는 text, JSON, XML, image, file endpoint를 함께 제공합니다.
    모든 endpoint의 schema가 같다고 가정하지 않고, 범용 path 호출과
    탐색 helper를 제공합니다.
    """

    def __init__(
        self,
        auth_key: str,
        *,
        timeout: float = 20,
        retries: int = 3,
        base_url: str = APIHUB_BASE_URL,
        session: Any | None = None,
        async_session: Any | None = None,
    ) -> None:
        self.auth_key = normalize_api_key(auth_key, field_name="auth_key")
        self.timeout = timeout
        self.retries = retries
        self.base_url = base_url.rstrip("/")
        self.session = session or build_session(retries)
        self._owns_session = session is None
        self._async_session = async_session
        self._owns_async_session = async_session is None

    @classmethod
    def from_env(cls, name: str = "KMA_APIHUB_AUTH_KEY", **kwargs: Any) -> ApiHubClient:
        auth_key = first_env_value((name, *APIHUB_ENV_NAMES))
        return cls(auth_key, **kwargs)

    @classmethod
    def aio(cls, auth_key: str, **kwargs: Any) -> ApiHubClient:
        """Create a client intended for async use."""

        return cls(auth_key, **kwargs)

    @classmethod
    def aio_from_env(cls, name: str = "KMA_APIHUB_AUTH_KEY", **kwargs: Any) -> ApiHubClient:
        """Create an async-capable client from environment credentials."""

        return cls.from_env(name=name, **kwargs)

    def close(self) -> None:
        close = getattr(self.session, "close", None)
        if self._owns_session and close is not None:
            close()

    async def aclose(self) -> None:
        if self._async_session is None or not self._owns_async_session:
            return
        aclose = getattr(self._async_session, "aclose", None)
        close = getattr(self._async_session, "close", None)
        if aclose is not None:
            await aclose()
        elif close is not None:
            close()

    def __enter__(self) -> ApiHubClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    async def __aenter__(self) -> ApiHubClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    def request_path(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
    ) -> ApiHubResponse:
        """`/api/...` 아래 APIHub path를 호출하고 `authKey`를 추가합니다."""

        clean_path = _normalize_apihub_path(path)
        request_params: dict[str, Any] = {}
        if params:
            request_params.update(params)
        request_params["authKey"] = self.auth_key
        return self._get(clean_path, request_params)

    async def arequest_path(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
    ) -> ApiHubResponse:
        """Asynchronously call an APIHub `/api/...` path."""

        clean_path = _normalize_apihub_path(path)
        request_params: dict[str, Any] = {}
        if params:
            request_params.update(params)
        request_params["authKey"] = self.auth_key
        return await self._aget(clean_path, request_params)

    def request_query_parts(
        self,
        path: str,
        query_parts: Iterable[tuple[str, str]],
        params: Mapping[str, Any] | None = None,
    ) -> ApiHubResponse:
        """이름 없는 query string 조각이 있는 APIHub endpoint를 호출합니다.

        일부 legacy 그래픽 endpoint는 ``...?202305031000&0&stn-list&authKey=...``
        같은 URL을 사용합니다. 일반적인 key-value query parameter가 아니므로
        `requests.get(..., params=...)`로 재현할 수 없습니다. `query_parts`는 각
        항목을 `("bare", name)` 또는 `("named", name)`으로 저장하고, 이 메서드는
        query string을 직접 직렬화합니다.
        """

        clean_path = _normalize_apihub_path(path)
        values = dict(params or {})
        fragments: list[str] = []
        for kind, name in query_parts:
            if name == "authKey":
                continue
            if name not in values:
                continue
            value = values[name]
            if value is None:
                continue
            if kind == "bare":
                fragments.append(_quote_query_value(value))
            else:
                fragments.append(f"{quote_plus(name)}={_quote_query_value(value)}")
        fragments.append(f"authKey={_quote_query_value(self.auth_key)}")
        return self._get_raw(f"{clean_path}?{'&'.join(fragments)}")

    async def arequest_query_parts(
        self,
        path: str,
        query_parts: Iterable[tuple[str, str]],
        params: Mapping[str, Any] | None = None,
    ) -> ApiHubResponse:
        """Asynchronously call an APIHub endpoint with ordered query parts."""

        clean_path = _normalize_apihub_path(path)
        values = dict(params or {})
        fragments: list[str] = []
        for kind, name in query_parts:
            if name == "authKey":
                continue
            if name not in values:
                continue
            value = values[name]
            if value is None:
                continue
            if kind == "bare":
                fragments.append(_quote_query_value(value))
            else:
                fragments.append(f"{quote_plus(name)}={_quote_query_value(value)}")
        fragments.append(f"authKey={_quote_query_value(self.auth_key)}")
        return await self._aget_raw(f"{clean_path}?{'&'.join(fragments)}")

    def open_api(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> ApiHubResponse:
        """`/api/typ02/openApi/{service}/{operation}` endpoint를 호출합니다."""

        request_params: dict[str, Any] = {
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)
        return self.request_path(
            f"/api/typ02/openApi/{service.strip('/')}/{operation.strip('/')}",
            request_params,
        )

    async def aopen_api(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> ApiHubResponse:
        """Asynchronously call `/api/typ02/openApi/{service}/{operation}`."""

        request_params: dict[str, Any] = {
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)
        return await self.arequest_path(
            f"/api/typ02/openApi/{service.strip('/')}/{operation.strip('/')}",
            request_params,
        )

    def discover_services(
        self,
        category_ids: tuple[int, ...] = APIHUB_CATEGORY_IDS,
    ) -> list[ApiHubService]:
        """공식 category id 목록에 대한 APIHub service 목록을 가져옵니다."""

        services: list[ApiHubService] = []
        for category_id in category_ids:
            response = self._portal_get("/apiList.do", {"seqApi": category_id})
            services.extend(parse_apihub_services(response.text, category_id))
        return services

    async def adiscover_services(
        self,
        category_ids: tuple[int, ...] = APIHUB_CATEGORY_IDS,
    ) -> list[ApiHubService]:
        """Asynchronously fetch APIHub service metadata."""

        services: list[ApiHubService] = []
        for category_id in category_ids:
            response = await self._aportal_get("/apiList.do", {"seqApi": category_id})
            services.extend(parse_apihub_services(response.text, category_id))
        return services

    def discover_endpoints(self, category_id: int, service_id: int) -> list[ApiHubEndpoint]:
        """하나의 APIHub service page에서 endpoint 예제를 가져옵니다."""

        response = self._portal_get(
            "/apiList.do",
            {"seqApi": category_id, "seqApiSub": service_id},
        )
        return extract_apihub_endpoints(response.text)

    async def adiscover_endpoints(
        self,
        category_id: int,
        service_id: int,
    ) -> list[ApiHubEndpoint]:
        """Asynchronously fetch endpoint samples for one APIHub service page."""

        response = await self._aportal_get(
            "/apiList.do",
            {"seqApi": category_id, "seqApiSub": service_id},
        )
        return extract_apihub_endpoints(response.text)

    def _portal_get(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        return self._get(path, params)

    async def _aportal_get(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        return await self._aget(path, params)

    def _get(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        return self._get_url(
            f"{self.base_url}/{path.lstrip('/')}",
            params=dict(params),
        )

    async def _aget(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        return await self._aget_url(
            f"{self.base_url}/{path.lstrip('/')}",
            params=dict(params),
        )

    def _get_raw(self, path_with_query: str) -> ApiHubResponse:
        return self._get_url(f"{self.base_url}/{path_with_query.lstrip('/')}", params=None)

    async def _aget_raw(self, path_with_query: str) -> ApiHubResponse:
        return await self._aget_url(f"{self.base_url}/{path_with_query.lstrip('/')}", params=None)

    def _get_url(self, url: str, params: Mapping[str, Any] | None) -> ApiHubResponse:
        endpoint = urlsplit(url).path
        metadata = make_response_metadata(
            provider="apihub",
            service_name="APIHub",
            endpoint=endpoint,
            request_params=params if params is not None else request_params_from_url(url),
        )
        try:
            response = get_with_retries(
                self.session,
                url,
                params=dict(params) if params is not None else None,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            message = _response_error_message(exc.response)
            suffix = f": {message}" if message else ""
            if status and status >= 500:
                raise KmaServerError(
                    f"APIHub server returned HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="server",
                    retryable=True,
                ) from None
            if status in {401, 403}:
                raise KmaAuthError(
                    f"APIHub request failed with HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="auth",
                    retryable=False,
                ) from None
            if status == 429:
                raise KmaRequestError(
                    f"APIHub request failed with HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="rate_limit",
                    retryable=True,
                ) from None
            raise KmaRequestError(
                f"APIHub request failed with HTTP {status}{suffix}",
                provider="apihub",
                endpoint=endpoint,
                status_code=status,
                failure_kind="request",
                retryable=False,
            ) from None
        except httpx.RequestError:
            raise KmaRequestError(
                "APIHub request failed",
                provider="apihub",
                endpoint=endpoint,
                failure_kind="network",
                retryable=True,
            ) from None

        content_type = response.headers.get("Content-Type", "")
        return ApiHubResponse(
            url=redact_url_credentials(str(response.url)),
            status_code=response.status_code,
            content_type=content_type,
            text=response.text,
            content=response.content,
            metadata=metadata,
        )

    async def _aget_url(self, url: str, params: Mapping[str, Any] | None) -> ApiHubResponse:
        endpoint = urlsplit(url).path
        metadata = make_response_metadata(
            provider="apihub",
            service_name="APIHub",
            endpoint=endpoint,
            request_params=params if params is not None else request_params_from_url(url),
        )
        try:
            response = await async_get_with_retries(
                self._get_async_session(),
                url,
                params=dict(params) if params is not None else None,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            message = _response_error_message(exc.response)
            suffix = f": {message}" if message else ""
            if status and status >= 500:
                raise KmaServerError(
                    f"APIHub server returned HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="server",
                    retryable=True,
                ) from None
            if status in {401, 403}:
                raise KmaAuthError(
                    f"APIHub request failed with HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="auth",
                    retryable=False,
                ) from None
            if status == 429:
                raise KmaRequestError(
                    f"APIHub request failed with HTTP {status}{suffix}",
                    provider="apihub",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="rate_limit",
                    retryable=True,
                ) from None
            raise KmaRequestError(
                f"APIHub request failed with HTTP {status}{suffix}",
                provider="apihub",
                endpoint=endpoint,
                status_code=status,
                failure_kind="request",
                retryable=False,
            ) from None
        except httpx.RequestError:
            raise KmaRequestError(
                "APIHub request failed",
                provider="apihub",
                endpoint=endpoint,
                failure_kind="network",
                retryable=True,
            ) from None

        content_type = response.headers.get("Content-Type", "")
        return ApiHubResponse(
            url=redact_url_credentials(str(response.url)),
            status_code=response.status_code,
            content_type=content_type,
            text=response.text,
            content=response.content,
            metadata=metadata,
        )

    def _get_async_session(self) -> Any:
        if self._async_session is None:
            self._async_session = build_async_client()
        return self._async_session


def parse_apihub_services(html_text: str, category_id: int) -> list[ApiHubService]:
    """APIHub의 `const apiList = [...]` service 목록을 파싱합니다."""

    match = re.search(r"const\s+apiList\s*=\s*(\[.*?\]);", html_text, re.S)
    if not match:
        return []
    try:
        raw_services = json.loads(match.group(1))
    except ValueError as exc:
        raise KmaParseError("Could not parse APIHub apiList JSON") from exc

    category_name = APIHUB_CATEGORIES.get(category_id, str(category_id))
    services: list[ApiHubService] = []
    for raw in raw_services:
        try:
            services.append(
                ApiHubService(
                    category_id=category_id,
                    category_name=category_name,
                    service_id=int(raw["seqApi"]),
                    service_name=str(raw["nmApi"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise KmaParseError(f"Malformed APIHub service entry: {raw!r}") from exc
    return services


def extract_apihub_endpoints(html_text: str) -> list[ApiHubEndpoint]:
    """APIHub service page에서 생성 API 예제 URL을 추출합니다."""

    endpoints: list[ApiHubEndpoint] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for raw in re.findall(r"https://apihub\.kma\.go\.kr/api/[^\s\"<>]+", html_text):
        endpoint = parse_apihub_sample_url(raw)
        key = (endpoint.path, endpoint.parameters)
        if key not in seen:
            endpoints.append(endpoint)
            seen.add(key)
    return endpoints


def parse_apihub_sample_url(raw_url: str) -> ApiHubEndpoint:
    """APIHub 예제 URL 하나를 path, parameter, 예제 값으로 파싱합니다."""

    cleaned = html.unescape(raw_url).replace("&amp;", "&")
    parts = urlsplit(cleaned)
    sample_params: dict[str, str] = {}
    parameters: list[str] = []
    query_parts = _parse_query_parts(parts.query)
    for kind, key in query_parts:
        if key == "authKey":
            continue
        value = _query_part_value(parts.query, kind, key)
        if key not in sample_params:
            parameters.append(key)
            sample_params[key] = value
    return ApiHubEndpoint(parts.path, tuple(parameters), sample_params, query_parts)


def parse_apihub_text_table(text: str, delimiter: str | None = None) -> ApiHubTextTable:
    """일반적인 APIHub text 응답을 comment와 dict row로 파싱합니다.

    APIHub text endpoint는 하나의 format으로 통일되어 있지 않습니다. delimiter가
    주어지면 CSV를 처리하고, header를 찾을 수 있는 공백 table을 처리하며,
    신뢰할 수 있는 header가 없으면 `_raw` row로 되돌립니다.
    """

    raw_lines = tuple(line.rstrip("\r") for line in text.splitlines())
    nonempty = [line.strip() for line in raw_lines if line.strip()]
    comments = tuple(line for line in nonempty if line.startswith("#"))
    data_lines = [line for line in nonempty if not line.startswith("#")]
    if not data_lines:
        return ApiHubTextTable((), (), comments, raw_lines)

    if delimiter is not None:
        reader = csv.DictReader(io.StringIO("\n".join(data_lines)), delimiter=delimiter)
        headers = tuple(reader.fieldnames or ())
        rows = tuple(dict(row) for row in reader)
        return ApiHubTextTable(headers, rows, comments, raw_lines)

    headers = _guess_text_headers(comments, data_lines)
    if not headers:
        rows = tuple({"_raw": line} for line in data_lines)
        return ApiHubTextTable((), rows, comments, raw_lines)

    rows_list: list[Mapping[str, str]] = []
    for line in data_lines:
        values = line.split()
        if len(values) < len(headers):
            rows_list.append({"_raw": line})
            continue
        if len(values) > len(headers):
            values = values[: len(headers) - 1] + [" ".join(values[len(headers) - 1 :])]
        rows_list.append(dict(zip(headers, values)))
    return ApiHubTextTable(headers, tuple(rows_list), comments, raw_lines)


def detect_image_info(content: bytes) -> tuple[str | None, int | None, int | None]:
    """일반적인 APIHub image bytes의 format과 pixel 크기를 반환합니다."""

    if content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) >= 24:
        return (
            "png",
            int.from_bytes(content[16:20], "big"),
            int.from_bytes(content[20:24], "big"),
        )
    if content[:6] in (b"GIF87a", b"GIF89a") and len(content) >= 10:
        return (
            "gif",
            int.from_bytes(content[6:8], "little"),
            int.from_bytes(content[8:10], "little"),
        )
    if content.startswith(b"\xff\xd8"):
        size = _detect_jpeg_size(content)
        if size is not None:
            return "jpeg", size[0], size[1]
        return "jpeg", None, None
    return None, None, None


def redact_url_credentials(url: str) -> str:
    """API credential query 값을 마스킹한 URL을 반환합니다."""

    parts = urlsplit(url)
    if not parts.query:
        return url
    redacted_parts: list[str] = []
    for raw_part in parts.query.split("&"):
        if "=" not in raw_part:
            redacted_parts.append(raw_part)
            continue
        key, _value = raw_part.split("=", 1)
        if is_credential_param(unquote_plus(key)):
            redacted_parts.append(f"{key}=***")
        else:
            redacted_parts.append(raw_part)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "&".join(redacted_parts), parts.fragment)
    )


def _response_error_message(response: Any) -> str:
    if response is None:
        return ""
    try:
        payload = response.json()
    except ValueError:
        text = str(getattr(response, "text", "")).strip()
        return redact_credentials_in_text(text[:200])
    if isinstance(payload, Mapping):
        result = payload.get("result")
        if isinstance(result, Mapping) and result.get("message"):
            return redact_credentials_in_text(str(result["message"]))
        response_body = payload.get("response")
        if isinstance(response_body, Mapping):
            header = response_body.get("header")
            if isinstance(header, Mapping) and header.get("resultMsg"):
                return redact_credentials_in_text(str(header["resultMsg"]))
    return ""


def _normalize_apihub_path(path: str) -> str:
    parts = urlsplit(path)
    clean = parts.path if parts.scheme or parts.netloc else path
    if not clean.startswith("/api/"):
        raise ValueError("APIHub path must start with /api/")
    return clean


def _parse_query_parts(query: str) -> tuple[tuple[str, str], ...]:
    parts: list[tuple[str, str]] = []
    bare_index = 1
    for raw_part in query.split("&"):
        if raw_part == "":
            continue
        if "=" in raw_part:
            key, _value = raw_part.split("=", 1)
            key = unquote_plus(key)
            if key == "authKey":
                continue
            parts.append(("named", key))
        else:
            parts.append(("bare", f"arg{bare_index}"))
            bare_index += 1
    return tuple(parts)


def _query_part_value(query: str, kind: str, name: str) -> str:
    bare_index = 1
    for raw_part in query.split("&"):
        if raw_part == "":
            continue
        if "=" in raw_part:
            key, value = raw_part.split("=", 1)
            if kind == "named" and unquote_plus(key) == name:
                return unquote_plus(value)
        else:
            current = f"arg{bare_index}"
            if kind == "bare" and current == name:
                return unquote_plus(raw_part)
            bare_index += 1
    return ""


def _quote_query_value(value: Any) -> str:
    return quote_plus(str(value), safe=",.:/")


def _guess_text_headers(comments: tuple[str, ...], data_lines: list[str]) -> tuple[str, ...]:
    for comment in reversed(comments):
        candidate = comment.lstrip("#").strip()
        if not candidate:
            continue
        fields = candidate.replace(",", " ").split()
        if len(fields) >= 2 and _looks_like_header(fields):
            return tuple(fields)
    if len(data_lines) >= 2:
        fields = data_lines[0].split()
        values = data_lines[1].split()
        if len(fields) >= 2 and len(values) >= len(fields) and _looks_like_header(fields):
            del data_lines[0]
            return tuple(fields)
    return ()


def _looks_like_header(fields: list[str]) -> bool:
    return any(re.search(r"[A-Za-z_가-힣]", field) for field in fields)


def _detect_jpeg_size(content: bytes) -> tuple[int, int] | None:
    index = 2
    while index + 9 < len(content):
        if content[index] != 0xFF:
            index += 1
            continue
        marker = content[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(content):
            return None
        length = int.from_bytes(content[index : index + 2], "big")
        if length < 2 or index + length > len(content):
            return None
        if 0xC0 <= marker <= 0xC3:
            height = int.from_bytes(content[index + 3 : index + 5], "big")
            width = int.from_bytes(content[index + 5 : index + 7], "big")
            return width, height
        index += length
    return None

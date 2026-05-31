"""HTTP client helpers backed by httpx."""

from __future__ import annotations

import asyncio
import time
from typing import Any, NoReturn

import httpx

from .exceptions import KmaAuthError, KmaRequestError, KmaServerError

RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


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
        try:
            response = client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if not _should_retry_status(exc) or attempt >= attempts - 1:
                raise
            last_exc = exc
        except httpx.RequestError as exc:
            if attempt >= attempts - 1:
                raise
            last_exc = exc
        time.sleep(backoff_factor * (2**attempt))
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
        try:
            response = await client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if not _should_retry_status(exc) or attempt >= attempts - 1:
                raise
            last_exc = exc
        except httpx.RequestError as exc:
            if attempt >= attempts - 1:
                raise
            last_exc = exc
        await asyncio.sleep(backoff_factor * (2**attempt))
    if last_exc is not None:  # pragma: no cover - defensive fallback
        raise last_exc
    raise RuntimeError("HTTP request failed before it could be attempted")


def _should_retry_status(exc: httpx.HTTPStatusError) -> bool:
    return exc.response.status_code in RETRY_STATUS_CODES

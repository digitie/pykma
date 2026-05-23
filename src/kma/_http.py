"""HTTP client helpers backed by httpx."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


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

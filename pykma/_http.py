"""HTTP session helpers."""

from __future__ import annotations

from typing import Any


def build_session(retries: int = 3) -> Any:
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "requests is required for KmaClient network calls. Install pykma with its "
            "project dependencies or pass a compatible custom session."
        ) from exc

    session = requests.Session()
    if retries <= 0:
        return session

    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

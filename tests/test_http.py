from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from kma import _http


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://example.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("boom", request=request, response=response)


class _FakeClient:
    """Sync client returning a queued sequence of status codes."""

    def __init__(self, statuses: list[int]) -> None:
        self._statuses = list(statuses)
        self.calls = 0

    def get(self, url: str, *, params: Any, timeout: float) -> _Resp:
        self.calls += 1
        status = self._statuses.pop(0)
        return _Resp(status)


class _AsyncFakeClient:
    def __init__(self, statuses: list[int]) -> None:
        self._statuses = list(statuses)
        self.calls = 0

    async def get(self, url: str, *, params: Any, timeout: float) -> _Resp:
        self.calls += 1
        status = self._statuses.pop(0)
        return _Resp(status)


def test_backoff_with_jitter_stays_within_equal_jitter_band() -> None:
    for attempt in range(5):
        base = 0.3 * (2**attempt)
        for _ in range(50):
            value = _http._backoff_with_jitter(0.3, attempt)
            assert base / 2 <= value <= base


def test_backoff_with_jitter_uses_random_uniform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_http.random, "uniform", lambda _a, b: b)
    # base = 0.3 * 2**2 = 1.2 -> half + half = base
    assert _http._backoff_with_jitter(0.3, 2) == pytest.approx(1.2)


def test_get_with_retries_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr(_http.time, "sleep", lambda s: slept.append(s))
    client = _FakeClient([503, 200])

    response = _http.get_with_retries(
        client, "http://example.test", params=None, timeout=1, retries=3
    )

    assert response.status_code == 200
    assert client.calls == 2
    assert len(slept) == 1  # one backoff between the two attempts


def test_get_with_retries_does_not_retry_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_http.time, "sleep", lambda s: None)
    client = _FakeClient([404, 200])

    with pytest.raises(httpx.HTTPStatusError):
        _http.get_with_retries(
            client, "http://example.test", params=None, timeout=1, retries=3
        )

    assert client.calls == 1  # 404 is not retryable


def test_get_with_retries_exhausts_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_http.time, "sleep", lambda s: None)
    client = _FakeClient([503, 503, 503])

    with pytest.raises(httpx.HTTPStatusError):
        _http.get_with_retries(
            client, "http://example.test", params=None, timeout=1, retries=2
        )

    assert client.calls == 3  # initial + 2 retries


def test_async_get_with_retries_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _no_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr(_http.asyncio, "sleep", _no_sleep)
    client = _AsyncFakeClient([502, 200])

    async def run() -> None:
        response = await _http.async_get_with_retries(
            client, "http://example.test", params=None, timeout=1, retries=3
        )
        assert response.status_code == 200
        assert client.calls == 2

    asyncio.run(run())

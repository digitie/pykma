from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import pykma.cli as cli
from pykma.time_utils import KST


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> None:
    try:
        func()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


@dataclass(frozen=True)
class FakeSnapshot:
    observed_at: datetime
    nx: int
    ny: int
    temperature: float


@dataclass(frozen=True)
class FakeForecast:
    forecast_at: datetime
    nx: int
    ny: int
    category: str
    value: float


class FakeClient:
    last_init_key: str | None = None
    last_from_env_called = False
    last_call: tuple[str, dict[str, Any]] | None = None

    def __init__(self, service_key: str) -> None:
        self.last_init_key = service_key
        FakeClient.last_init_key = service_key

    @classmethod
    def from_env(cls) -> FakeClient:
        cls.last_from_env_called = True
        return cls("env-key")

    def now(self, **kwargs: Any) -> FakeSnapshot:
        FakeClient.last_call = ("now", kwargs)
        return FakeSnapshot(datetime(2026, 4, 30, 14, 0, tzinfo=KST), 60, 127, 18.4)

    def forecast(self, **kwargs: Any) -> list[FakeForecast]:
        FakeClient.last_call = ("forecast", kwargs)
        return [FakeForecast(datetime(2026, 4, 30, 15, 0, tzinfo=KST), 60, 127, "TMP", 18.4)]

    def forecast_short(self, **kwargs: Any) -> list[FakeForecast]:
        FakeClient.last_call = ("forecast_short", kwargs)
        return [FakeForecast(datetime(2026, 4, 30, 15, 0, tzinfo=KST), 60, 127, "T1H", 18.4)]


class FakeApiHubResponse:
    text = "hub-ok"


class FakeApiHubClient:
    last_init_key: str | None = None
    last_from_env_called = False
    last_call: tuple[str, dict[str, str]] | None = None

    def __init__(self, auth_key: str) -> None:
        FakeApiHubClient.last_init_key = auth_key

    @classmethod
    def from_env(cls) -> FakeApiHubClient:
        cls.last_from_env_called = True
        return cls("env-hub-key")

    def request_path(self, path: str, params: dict[str, str]) -> FakeApiHubResponse:
        FakeApiHubClient.last_call = (path, params)
        return FakeApiHubResponse()


def test_cli_now_outputs_json_and_uses_explicit_service_key() -> None:
    original = cli.KmaClient
    cli.KmaClient = FakeClient  # type: ignore[assignment]
    stream = io.StringIO()
    try:
        with redirect_stdout(stream):
            result = cli.main(["--service-key", "decoded-key", "now", "--nx", "60", "--ny", "127"])
    finally:
        cli.KmaClient = original

    assert result == 0
    assert FakeClient.last_init_key == "decoded-key"
    assert FakeClient.last_call == ("now", {"nx": 60, "ny": 127})
    payload = json.loads(stream.getvalue())
    assert payload["temperature"] == 18.4
    assert payload["observed_at"] == "2026-04-30 14:00:00+09:00"


def test_cli_forecast_short_uses_from_env_and_latlon() -> None:
    original = cli.KmaClient
    cli.KmaClient = FakeClient  # type: ignore[assignment]
    FakeClient.last_from_env_called = False
    stream = io.StringIO()
    try:
        with redirect_stdout(stream):
            result = cli.main(
                ["forecast", "--short", "--lat", "37.5665", "--lon", "126.9780"]
            )
    finally:
        cli.KmaClient = original

    assert result == 0
    assert FakeClient.last_from_env_called is True
    assert FakeClient.last_call == ("forecast_short", {"lat": 37.5665, "lon": 126.978})
    payload = json.loads(stream.getvalue())
    assert payload[0]["category"] == "T1H"


def test_cli_rejects_incomplete_location_pairs() -> None:
    assert_raises(SystemExit, lambda: cli.main(["now", "--lat", "37.5"]))
    assert_raises(SystemExit, lambda: cli.main(["now", "--nx", "60"]))


def test_cli_apihub_calls_generic_path() -> None:
    original = cli.ApiHubClient
    cli.ApiHubClient = FakeApiHubClient  # type: ignore[assignment]
    FakeApiHubClient.last_from_env_called = False
    stream = io.StringIO()
    try:
        with redirect_stdout(stream):
            result = cli.main(
                [
                    "apihub",
                    "/api/typ01/url/kma_sfctm2.php",
                    "--param",
                    "tm=202211300900",
                    "--param",
                    "stn=108",
                ]
            )
    finally:
        cli.ApiHubClient = original

    assert result == 0
    assert stream.getvalue().strip() == "hub-ok"
    assert FakeApiHubClient.last_from_env_called is True
    assert FakeApiHubClient.last_call == (
        "/api/typ01/url/kma_sfctm2.php",
        {"tm": "202211300900", "stn": "108"},
    )


def test_cli_apihub_rejects_bad_param_shape() -> None:
    assert_raises(
        SystemExit,
        lambda: cli.main(["apihub", "/api/typ01/url/kma_sfctm2.php", "--param", "bad"]),
    )

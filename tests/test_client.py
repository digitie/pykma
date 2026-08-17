from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from kma.client import KmaClient
from kma.enums import WeatherCategory
from kma.exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from kma.locations import GridPoint, LatLon
from kma.time_utils import KST

T = TypeVar("T", bound=BaseException)


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    @property
    def last_params(self) -> dict[str, Any] | None:
        if not self.calls:
            return None
        return self.calls[-1]["params"]

    @property
    def last_url(self) -> str | None:
        if not self.calls:
            return None
        return self.calls[-1]["url"]

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)


class AsyncFakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)

    async def aclose(self) -> None:
        self.closed = True


def assert_raises(exc_type: type[T], func: Callable[[], object]) -> T:
    try:
        func()
    except exc_type as exc:
        return exc
    except Exception as exc:  # pragma: no cover - failure path for clearer direct-run output
        raise AssertionError(f"expected {exc_type.__name__}, got {type(exc).__name__}") from exc
    raise AssertionError(f"expected {exc_type.__name__}")


def _payload(items: Any) -> dict[str, Any]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {"items": {"item": items}},
        }
    }


def _error_payload(code: str, message: str = "ERROR") -> dict[str, Any]:
    return {
        "response": {
            "header": {"resultCode": code, "resultMsg": message},
            "body": {},
        }
    }


def test_now_pivots_observed_items() -> None:
    session = FakeSession(
        _payload(
            [
                {"category": "T1H", "obsrValue": "18.4"},
                {"category": "REH", "obsrValue": "52"},
                {"category": "WSD", "obsrValue": "3.1"},
                {"category": "VEC", "obsrValue": "270"},
                {"category": "RN1", "obsrValue": "강수없음"},
                {"category": "PTY", "obsrValue": "0"},
            ]
        )
    )
    client = KmaClient("decoded-key", session=session)

    snapshot = client.now(nx=60, ny=127, when=datetime(2026, 4, 30, 14, 45, tzinfo=KST))

    assert snapshot.observed_at.isoformat() == "2026-04-30T14:00:00+09:00"
    assert snapshot.temperature == 18.4
    assert snapshot.humidity == 52
    assert snapshot.wind_speed == 3.1
    assert snapshot.wind_direction == 270
    assert snapshot.precipitation == 0.0
    assert snapshot.precipitation_label == "없음"
    assert snapshot.metadata is not None
    assert snapshot.metadata.provider == "data.go.kr"
    assert snapshot.metadata.service_name == "VilageFcstInfoService_2.0"
    assert snapshot.metadata.endpoint == "getUltraSrtNcst"
    assert snapshot.metadata.base_date == "20260430"
    assert snapshot.metadata.base_time == "1400"
    assert "serviceKey" not in snapshot.metadata.request_params
    assert session.last_params is not None
    assert session.last_params["serviceKey"] == "decoded-key"
    assert session.last_params["base_date"] == "20260430"
    assert session.last_params["base_time"] == "1400"
    assert session.last_params["dataType"] == "JSON"


def test_forecast_service_matches_krheritage_style_facade() -> None:
    session = FakeSession(
        _payload(
            {
                "baseDate": "20260430",
                "baseTime": "1400",
                "fcstDate": "20260430",
                "fcstTime": "1500",
                "nx": "60",
                "ny": "127",
                "category": "TMP",
                "fcstValue": "18.4",
            }
        )
    )
    client = KmaClient("decoded-key", session=session)

    items = client.forecast.vilage(
        nx=60,
        ny=127,
        when=datetime(2026, 4, 30, 14, 15, tzinfo=KST),
    )

    assert items[0].value == 18.4
    assert (
        client.forecast(nx=60, ny=127, when=datetime(2026, 4, 30, 14, 15, tzinfo=KST))[0].value
        == 18.4
    )
    assert session.last_params is not None
    assert session.last_params["base_time"] == "1400"


def test_aio_client_exposes_async_forecast_service() -> None:
    async def run() -> None:
        session = AsyncFakeSession(
            _payload(
                [
                    {"category": "T1H", "obsrValue": "18.4"},
                    {"category": "REH", "obsrValue": "52"},
                    {"category": "PTY", "obsrValue": "0"},
                ]
            )
        )

        async with KmaClient.aio("decoded-key", async_session=session) as client:
            snapshot = await client.forecast.now(
                nx=60,
                ny=127,
                when=datetime(2026, 4, 30, 14, 45, tzinfo=KST),
            )

        assert snapshot.temperature == 18.4
        assert session.calls[0]["params"]["serviceKey"] == "decoded-key"
        assert session.closed is False
        assert client.closed is True

    asyncio.run(run())


def test_client_service_key_strips_copied_whitespace() -> None:
    session = FakeSession(_payload({"version": "202604301400"}))
    client = KmaClient(" decoded \n key\t", session=session)

    client.version("ODAM", when=datetime(2026, 4, 30, 14, 0, tzinfo=KST))

    assert session.last_params is not None
    assert session.last_params["serviceKey"] == "decodedkey"


def test_forecast_uses_latlon_conversion_and_preserves_pcp_labels() -> None:
    session = FakeSession(
        _payload(
            [
                {
                    "baseDate": "20260430",
                    "baseTime": "1400",
                    "fcstDate": "20260430",
                    "fcstTime": "1500",
                    "nx": "60",
                    "ny": "127",
                    "category": "TMP",
                    "fcstValue": "18.4",
                },
                {
                    "baseDate": "20260430",
                    "baseTime": "1400",
                    "fcstDate": "20260430",
                    "fcstTime": "1500",
                    "nx": "60",
                    "ny": "127",
                    "category": "PCP",
                    "fcstValue": "1.0mm 미만",
                },
                {
                    "baseDate": "20260430",
                    "baseTime": "1400",
                    "fcstDate": "20260430",
                    "fcstTime": "1500",
                    "nx": "60",
                    "ny": "127",
                    "category": "SKY",
                    "fcstValue": "1",
                },
            ]
        )
    )
    client = KmaClient("decoded-key", session=session)

    items = client.forecast(
        lat=37.5665,
        lon=126.9780,
        when=datetime(2026, 4, 30, 14, 15, tzinfo=KST),
    )

    assert session.last_params is not None
    assert session.last_params["nx"] == 60
    assert session.last_params["ny"] == 127
    assert session.last_params["base_time"] == "1400"
    assert items[0].value == 18.4
    assert items[1].value == "1.0mm 미만"
    assert items[1].raw["fcstValue"] == "1.0mm 미만"
    assert items[1].metadata is not None
    assert "serviceKey" not in items[1].metadata.request_params
    assert items[2].label == "맑음"


def test_client_accepts_standard_location_objects_and_returns_category_enums() -> None:
    session = FakeSession(
        _payload(
            [
                {
                    "baseDate": "20260430",
                    "baseTime": "1400",
                    "fcstDate": "20260430",
                    "fcstTime": "1500",
                    "nx": "60",
                    "ny": "127",
                    "category": "TMP",
                    "fcstValue": "18.4",
                }
            ]
        )
    )
    client = KmaClient("decoded-key", session=session)

    items = client.forecast(
        location=LatLon(37.5665, 126.9780),
        when=datetime(2026, 4, 30, 14, 15, tzinfo=KST),
    )

    assert session.last_params is not None
    assert session.last_params["nx"] == 60
    assert session.last_params["ny"] == 127
    assert items[0].category is WeatherCategory.TEMPERATURE
    assert items[0].category == "TMP"
    assert items[0].category_enum is WeatherCategory.TEMPERATURE
    assert items[0].unit == "C"
    assert items[0].grid == GridPoint(60, 127)
    assert isinstance(items[0].latlon, LatLon)


def test_client_accepts_grid_location_mapping() -> None:
    session = FakeSession(
        _payload(
            [
                {"category": "T1H", "obsrValue": "18.4"},
                {"category": "PTY", "obsrValue": "0"},
            ]
        )
    )
    client = KmaClient("decoded-key", session=session)

    snapshot = client.now(
        location={"nx": "60", "ny": "127"},
        when=datetime(2026, 4, 30, 14, 45, tzinfo=KST),
    )

    assert snapshot.grid == GridPoint(60, 127)
    assert isinstance(snapshot.latlon, LatLon)
    assert snapshot.temperature == 18.4


def test_fetch_items_accepts_single_item_dict() -> None:
    session = FakeSession(
        _payload(
            {
                "baseDate": "20260430",
                "baseTime": "1430",
                "fcstDate": "20260430",
                "fcstTime": "1500",
                "nx": "60",
                "ny": "127",
                "category": "PTY",
                "fcstValue": "4",
            }
        )
    )
    client = KmaClient("decoded-key", session=session)

    items = client.forecast_short(nx=60, ny=127, when=datetime(2026, 4, 30, 14, 50, tzinfo=KST))

    assert len(items) == 1
    assert items[0].label == "소나기"


def test_version_converts_aware_datetime_to_kst() -> None:
    session = FakeSession(
        {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
                "body": {"items": {"item": []}},
            }
        }
    )
    client = KmaClient("decoded-key", session=session)

    client.version("ODAM", datetime(2026, 4, 30, 5, 30, tzinfo=timezone.utc))

    assert session.last_url is not None
    assert session.last_url.endswith("/getFcstVersion")
    assert session.last_params is not None
    assert session.last_params["basedatetime"] == "202604301430"


def test_coordinate_validation_rejects_partial_mixed_and_out_of_range_inputs() -> None:
    client = KmaClient("decoded-key", session=FakeSession(_payload([])))

    assert_raises(ValueError, lambda: client.now(lat=37.5))
    assert_raises(ValueError, lambda: client.now(nx=60))
    assert_raises(ValueError, lambda: client.now(lat=37.5, lon=127.0, nx=60, ny=127))
    assert_raises(ValueError, lambda: client.now(lat=91.0, lon=127.0))
    assert_raises(ValueError, lambda: client.now(nx=0, ny=127))
    assert_raises(ValueError, lambda: client.now(nx=60, ny=254))


def test_result_codes_raise_typed_exceptions() -> None:
    auth_codes = {"20", "30", "31"}
    server_codes = {"04", "99"}
    # `22`는 quota라 아래에서 따로 본다. 예전에는 `12`와 한 묶음이었고
    # `failure_kind`도 `retryable`도 단언하지 않아, `22`가 `retryable=True`로
    # 잘못 분류된 채 이 테스트를 통과했다.
    request_codes = {"12"}

    for code in auth_codes:
        client = KmaClient("bad-key", session=FakeSession(_error_payload(code)))
        error = assert_raises(KmaAuthError, lambda client=client: client.now(nx=60, ny=127))
        assert error.failure_kind == "auth"
        assert error.result_code == code
        assert error.retryable is False

    for code in server_codes:
        client = KmaClient("decoded-key", session=FakeSession(_error_payload(code)))
        error = assert_raises(KmaServerError, lambda client=client: client.now(nx=60, ny=127))
        assert error.failure_kind == "server"
        assert error.retryable is True

    for code in request_codes:
        client = KmaClient("decoded-key", session=FakeSession(_error_payload(code)))
        error = assert_raises(KmaRequestError, lambda client=client: client.now(nx=60, ny=127))
        assert error.provider == "data.go.kr"
        assert error.endpoint == "getUltraSrtNcst"
        assert error.failure_kind == "request"
        assert error.retryable is False

    # 일일 quota 초과. 한도는 자정에 리셋되므로 **당일 재시도는 성공할 수 없다** —
    # `retryable=True`면 호출자가 성공 못 할 것에 retry budget을 태운다.
    quota_client = KmaClient("decoded-key", session=FakeSession(_error_payload("22")))
    quota_error = assert_raises(
        KmaRequestError, lambda: quota_client.now(nx=60, ny=127)
    )
    assert quota_error.result_code == "22"
    assert quota_error.failure_kind == "quota"
    assert quota_error.retryable is False


def test_no_data_result_code_returns_empty_forecast() -> None:
    client = KmaClient("decoded-key", session=FakeSession(_error_payload("03", "NO_DATA")))

    items = client.forecast_short(
        nx=60,
        ny=127,
        when=datetime(2026, 4, 30, 14, 50, tzinfo=KST),
    )

    assert items == []


def test_no_data_result_code_returns_empty_snapshot() -> None:
    client = KmaClient("decoded-key", session=FakeSession(_error_payload("03", "NO_DATA")))

    snapshot = client.now(nx=60, ny=127, when=datetime(2026, 4, 30, 14, 45, tzinfo=KST))

    assert snapshot.temperature is None
    assert snapshot.humidity is None
    assert snapshot.raw["items"] == []


def test_malformed_envelope_raises_parse_error() -> None:
    client = KmaClient("decoded-key", session=FakeSession({"not_response": {}}))

    assert_raises(KmaParseError, lambda: client.now(nx=60, ny=127))


def test_missing_items_raises_parse_error() -> None:
    client = KmaClient(
        "decoded-key",
        session=FakeSession(
            {
                "response": {
                    "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
                    "body": {},
                }
            }
        ),
    )

    assert_raises(KmaParseError, lambda: client.now(nx=60, ny=127))


def test_malformed_forecast_item_raises_parse_error() -> None:
    client = KmaClient(
        "decoded-key",
        session=FakeSession(
            _payload(
                [
                    {
                        "baseDate": "20260430",
                        "baseTime": "1400",
                        "fcstDate": "20260430",
                        "fcstTime": "1500",
                        "nx": "60",
                        "ny": "127",
                        "fcstValue": "18.4",
                    }
                ]
            )
        ),
    )

    assert_raises(KmaParseError, lambda: client.forecast(nx=60, ny=127))

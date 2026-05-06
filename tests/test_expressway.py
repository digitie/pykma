from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from pykma import ExpresswayRestAreaWeatherClient, RestAreaWeather
from pykma.exceptions import KmaAuthError, KmaParseError
from pykma.time_utils import KST


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = payloads
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        index = min(len(self.calls) - 1, len(self.payloads) - 1)
        return FakeResponse(self.payloads[index])


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> BaseException:
    try:
        func()
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def _row(**overrides: Any) -> dict[str, Any]:
    row = {
        "sdate": "20210507",
        "stdHour": "12",
        "unitCode": "002 ",
        "unitName": "죽전휴게소",
        "routeNo": "0010",
        "routeName": "경부선",
        "updownTypeCode": "E",
        "xValue": "127.104165",
        "yValue": "37.332651",
        "addr": "경기도 용인시 수지구 풍덕천동 42-1",
        "measurement": "연천",
        "weatherContents": "비끝남",
        "tempValue": "14.500000",
        "humidityValue": "66.000000",
        "windValue": "4.400000",
        "windContents": "23",
        "rainfallValue": "8.900000",
        "rainfallstrengthValue": "-99.000000",
        "newsnowValue": "-99.000000",
        "snowValue": "-99.000000",
        "cloudValue": "9.000000",
        "dewValue": "8.200000",
    }
    row.update(overrides)
    return row


def _payload(rows: list[dict[str, Any]] | None) -> dict[str, Any]:
    return {
        "count": 0 if rows is None else len(rows),
        "list": rows,
        "message": "인증키가 유효합니다.",
        "code": "SUCCESS",
    }


def test_expressway_weather_request_builds_params_and_parses_rows() -> None:
    session = FakeSession([_payload([_row()])])
    client = ExpresswayRestAreaWeatherClient("road-key", session=session)

    rows = client.weather(sdate="20210507", std_hour=12)

    assert len(rows) == 1
    item = rows[0]
    assert isinstance(item, RestAreaWeather)
    assert item.observed_at.isoformat() == "2021-05-07T12:00:00+09:00"
    assert item.unit_code == "002"
    assert item.unit_name == "죽전휴게소"
    assert item.route_name == "경부선"
    assert item.weather == "비끝남"
    assert item.temperature == 14.5
    assert item.humidity == 66.0
    assert item.wind_speed == 4.4
    assert item.rainfall == 8.9
    assert item.rainfall_strength is None
    assert item.snow is None
    assert item.latlon is not None
    assert item.latlon.lat == 37.332651
    assert item.latlon.lon == 127.104165
    assert session.calls[0]["url"] == "http://data.ex.co.kr/openapi/restinfo/restWeatherList"
    assert session.calls[0]["params"] == {
        "key": "road-key",
        "type": "json",
        "sdate": "20210507",
        "stdHour": "12",
    }


def test_expressway_empty_or_null_list_returns_empty_rows() -> None:
    assert ExpresswayRestAreaWeatherClient(
        "road-key",
        session=FakeSession([_payload([])]),
    ).weather(sdate="20210507", std_hour="12") == []
    assert ExpresswayRestAreaWeatherClient(
        "road-key",
        session=FakeSession([_payload(None)]),
    ).weather(sdate="20210507", std_hour="12") == []


def test_expressway_latest_weather_looks_back_until_non_empty() -> None:
    session = FakeSession([_payload([]), _payload([_row(stdHour="11")])])
    client = ExpresswayRestAreaWeatherClient("road-key", session=session)

    rows = client.latest_weather(
        when=datetime(2021, 5, 7, 12, 30, tzinfo=KST),
        lookback_hours=2,
    )

    assert rows[0].std_hour == "11"
    assert session.calls[0]["params"]["stdHour"] == "12"
    assert session.calls[1]["params"]["stdHour"] == "11"


def test_expressway_result_code_and_shape_errors() -> None:
    auth_client = ExpresswayRestAreaWeatherClient(
        "bad-key",
        session=FakeSession([{"list": None, "count": 0, "message": "인증키가 유효하지 않습니다.", "code": "ERROR"}]),
    )
    shape_client = ExpresswayRestAreaWeatherClient(
        "road-key",
        session=FakeSession([{"list": "bad", "count": 1, "message": "ok", "code": "SUCCESS"}]),
    )

    error = assert_raises(KmaAuthError, lambda: auth_client.weather(sdate="20210507", std_hour=12))
    assert "bad-key" not in str(error)
    assert_raises(KmaParseError, lambda: shape_client.weather(sdate="20210507", std_hour=12))


def test_expressway_validates_date_and_hour() -> None:
    client = ExpresswayRestAreaWeatherClient("road-key", session=FakeSession([_payload([])]))

    assert_raises(ValueError, lambda: client.weather(sdate="2021-05-07", std_hour=12))
    assert_raises(ValueError, lambda: client.weather(sdate="20210507", std_hour=24))
    assert_raises(ValueError, lambda: client.latest_weather(lookback_hours=-1))


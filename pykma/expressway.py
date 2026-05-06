"""Client for Korea Expressway Corporation rest-area weather data."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Mapping, Optional

from ._http import build_session
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .models import RestAreaWeather
from .time_utils import KST, as_kst

try:
    import requests
    from requests import HTTPError, RequestException
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore[assignment]
    HTTPError = ()  # type: ignore[assignment]
    RequestException = ()  # type: ignore[assignment]

EXPRESSWAY_REST_AREA_WEATHER_URL = "http://data.ex.co.kr/openapi/restinfo/restWeatherList"


class ExpresswayRestAreaWeatherClient:
    """Client for Korea Expressway Corporation rest-area weather API."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: str = EXPRESSWAY_REST_AREA_WEATHER_URL,
        session: Optional[Any] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = base_url
        self.session = session or build_session(retries)

    @classmethod
    def from_env(
        cls,
        name: str = "EXPRESSWAY_API_KEY",
        **kwargs: Any,
    ) -> "ExpresswayRestAreaWeatherClient":
        api_key = os.getenv(name) or os.getenv("KOREA_EXPRESSWAY_API_KEY")
        if not api_key:
            raise ValueError(f"{name} or KOREA_EXPRESSWAY_API_KEY is not set")
        return cls(api_key, **kwargs)

    def request(
        self,
        *,
        sdate: str | date | datetime,
        std_hour: str | int,
        response_type: str = "json",
    ) -> Mapping[str, Any]:
        """Call the raw rest-area weather endpoint and return its JSON payload."""

        params = {
            "key": self.api_key,
            "type": response_type,
            "sdate": _format_sdate(sdate),
            "stdHour": _format_hour(std_hour),
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(f"Expressway server returned HTTP {status}") from None
            raise KmaRequestError(f"Expressway request failed with HTTP {status}") from None
        except RequestException:
            raise KmaRequestError("Expressway request failed") from None

        try:
            payload = response.json()
        except ValueError as exc:
            raise KmaParseError("Expressway response was not JSON") from exc
        if not isinstance(payload, Mapping):
            raise KmaParseError("Expressway response was not an object")
        _raise_for_expressway_code(payload)
        return payload

    def weather(
        self,
        *,
        sdate: str | date | datetime,
        std_hour: str | int,
    ) -> list[RestAreaWeather]:
        """Return rest-area weather rows as typed dataclasses."""

        payload = self.request(sdate=sdate, std_hour=std_hour)
        rows = payload.get("list", [])
        if rows is None:
            return []
        if not isinstance(rows, list):
            raise KmaParseError("Expressway response list was not a list")
        return [_rest_area_weather(row) for row in rows]

    def latest_weather(
        self,
        *,
        when: Optional[datetime] = None,
        lookback_hours: int = 48,
    ) -> list[RestAreaWeather]:
        """Return the newest non-empty rest-area weather rows within a lookback window."""

        if lookback_hours < 0:
            raise ValueError("lookback_hours must be >= 0")
        base = as_kst(when) if when is not None else datetime.now(KST)
        base = base.replace(minute=0, second=0, microsecond=0)
        for offset in range(lookback_hours + 1):
            target = base - timedelta(hours=offset)
            rows = self.weather(sdate=target, std_hour=target.hour)
            if rows:
                return rows
        return []


def _rest_area_weather(row: object) -> RestAreaWeather:
    if not isinstance(row, Mapping):
        raise KmaParseError(f"Malformed Expressway weather row: {row!r}")
    try:
        return RestAreaWeather(
            observed_at=_parse_observed_at(row.get("sdate"), row.get("stdHour")),
            sdate=_clean_str(row.get("sdate")),
            std_hour=_format_hour(_clean_str(row.get("stdHour"))),
            unit_code=_clean_str(row.get("unitCode")),
            unit_name=_clean_str(row.get("unitName")),
            route_no=_clean_str(row.get("routeNo")),
            route_name=_clean_str(row.get("routeName")),
            direction_code=_str_or_none(row.get("updownTypeCode")),
            longitude=_float_or_none(row.get("xValue")),
            latitude=_float_or_none(row.get("yValue")),
            address=_str_or_none(row.get("addr")),
            measurement_station=_str_or_none(row.get("measurement")),
            weather=_str_or_none(row.get("weatherContents")),
            temperature=_float_or_none(row.get("tempValue")),
            humidity=_float_or_none(row.get("humidityValue")),
            wind_speed=_float_or_none(row.get("windValue")),
            wind_direction_code=_str_or_none(row.get("windContents")),
            rainfall=_float_or_none(row.get("rainfallValue")),
            rainfall_strength=_float_or_none(row.get("rainfallstrengthValue")),
            new_snow=_float_or_none(row.get("newsnowValue")),
            snow=_float_or_none(row.get("snowValue")),
            cloud=_float_or_none(row.get("cloudValue")),
            dew_point=_float_or_none(row.get("dewValue")),
            raw=dict(row),
        )
    except (TypeError, ValueError) as exc:
        raise KmaParseError(f"Malformed Expressway weather row: {row!r}") from exc


def _raise_for_expressway_code(payload: Mapping[str, Any]) -> None:
    code = str(payload.get("code", ""))
    message = str(payload.get("message", ""))
    if code in {"", "SUCCESS"}:
        return
    text = f"Expressway API returned {code}: {message}"
    if "인증키" in message:
        raise KmaAuthError(text)
    raise KmaRequestError(text)


def _format_sdate(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return as_kst(value).strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    if len(text) != 8 or not text.isdigit():
        raise ValueError("sdate must be YYYYMMDD")
    return text


def _format_hour(value: str | int) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError("std_hour must not be empty")
    hour = int(text)
    if not 0 <= hour <= 23:
        raise ValueError("std_hour must be between 0 and 23")
    return f"{hour:02d}"


def _parse_observed_at(sdate: object, std_hour: object) -> datetime:
    raw = f"{_format_sdate(str(sdate))}{_format_hour(str(std_hour))}"
    return datetime.strptime(raw, "%Y%m%d%H").replace(tzinfo=KST)


def _clean_str(value: object) -> str:
    return "" if value is None else str(value).strip()


def _str_or_none(value: object) -> str | None:
    text = _clean_str(value)
    return text or None


def _float_or_none(value: object) -> float | None:
    text = _clean_str(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number <= -99.0:
        return None
    return number

"""Public KMA API client."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Mapping, Optional

try:
    import requests
    from requests import HTTPError, RequestException
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal envs
    requests = None  # type: ignore[assignment]
    HTTPError = ()  # type: ignore[assignment]
    RequestException = ()  # type: ignore[assignment]

from ._http import build_session
from .codes import label_for, normalize_value, parse_amount
from .enums import KmaEndpoint, WeatherCategory, coerce_category, enum_value
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .grid import validate_grid
from .locations import LocationInput, normalize_location
from .models import ForecastItem, WeatherSnapshot
from .time_utils import (
    as_kst,
    latest_ultra_srt_fcst_base,
    latest_ultra_srt_ncst_base,
    latest_vilage_base,
    parse_kma_datetime,
)

DEFAULT_BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"


class KmaClient:
    """Client for KMA VilageFcstInfoService_2.0 endpoints."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: Optional[str] = None,
        session: Optional[Any] = None,
    ) -> None:
        if not service_key:
            raise ValueError("service_key is required")
        self.service_key = service_key
        self.timeout = timeout
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.session = session or build_session(retries)

    @classmethod
    def from_env(cls, name: str = "KMA_SERVICE_KEY", **kwargs: Any) -> "KmaClient":
        try:
            service_key = os.environ[name]
        except KeyError as exc:
            raise ValueError(f"{name} is not set") from exc
        return cls(service_key=service_key, **kwargs)

    def now(
        self,
        *,
        location: Optional[LocationInput] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        nx: Optional[int] = None,
        ny: Optional[int] = None,
        when: Optional[datetime] = None,
    ) -> WeatherSnapshot:
        """Fetch current ultra-short observations.

        Uses `getUltraSrtNcst` and automatically selects the latest usable KST
        base time when `when` is omitted.
        """

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_ncst_base(when)
        items = self._fetch_items(
            KmaEndpoint.ULTRA_SRT_NCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        by_category = {str(item.get("category")): item.get("obsrValue") for item in items}
        raw = {"items": items, "by_category": by_category}

        return WeatherSnapshot(
            observed_at=parse_kma_datetime(base_date, base_time),
            nx=grid_x,
            ny=grid_y,
            temperature=_float_or_none(
                by_category.get(WeatherCategory.CURRENT_TEMPERATURE.value)
            ),
            humidity=_int_or_none(by_category.get(WeatherCategory.HUMIDITY.value)),
            wind_speed=_float_or_none(by_category.get(WeatherCategory.WIND_SPEED.value)),
            wind_direction=_int_or_none(by_category.get(WeatherCategory.WIND_DIRECTION.value)),
            precipitation=parse_amount(by_category.get(WeatherCategory.ONE_HOUR_RAIN.value)),
            sky_label=label_for(
                WeatherCategory.SKY,
                by_category.get(WeatherCategory.SKY.value),
                endpoint=KmaEndpoint.ULTRA_SRT_NCST,
            ),
            precipitation_label=label_for(
                WeatherCategory.PRECIPITATION_TYPE,
                by_category.get(WeatherCategory.PRECIPITATION_TYPE.value),
                endpoint=KmaEndpoint.ULTRA_SRT_NCST,
            ),
            raw=raw,
        )

    def forecast_short(
        self,
        *,
        location: Optional[LocationInput] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        nx: Optional[int] = None,
        ny: Optional[int] = None,
        when: Optional[datetime] = None,
    ) -> list[ForecastItem]:
        """Fetch ultra-short forecast items from `getUltraSrtFcst`."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_fcst_base(when)
        items = self._fetch_items(
            KmaEndpoint.ULTRA_SRT_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [_forecast_item(item, KmaEndpoint.ULTRA_SRT_FCST) for item in items]

    def forecast(
        self,
        *,
        location: Optional[LocationInput] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        nx: Optional[int] = None,
        ny: Optional[int] = None,
        when: Optional[datetime] = None,
    ) -> list[ForecastItem]:
        """Fetch village forecast items from `getVilageFcst`."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_vilage_base(when)
        items = self._fetch_items(
            KmaEndpoint.VILAGE_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [_forecast_item(item, KmaEndpoint.VILAGE_FCST) for item in items]

    def version(self, ftype: str, when: datetime) -> Mapping[str, Any]:
        """Fetch forecast version metadata from `getFcstVersion`."""

        when_kst = as_kst(when)
        base_date = when_kst.strftime("%Y%m%d")
        base_time = when_kst.strftime("%H%M")
        items = self._request(
            KmaEndpoint.FCST_VERSION,
            {
                "ftype": ftype,
                "basedatetime": f"{base_date}{base_time}",
            },
        )
        return items

    def _coordinates(
        self,
        *,
        location: Optional[LocationInput],
        lat: Optional[float],
        lon: Optional[float],
        nx: Optional[int],
        ny: Optional[int],
    ) -> tuple[int, int]:
        grid = normalize_location(location, lat=lat, lon=lon, nx=nx, ny=ny)
        return grid.nx, grid.ny

    def _fetch_items(
        self,
        endpoint: str | KmaEndpoint,
        *,
        base_date: str,
        base_time: str,
        nx: int,
        ny: int,
    ) -> list[Mapping[str, Any]]:
        body = self._request(
            endpoint,
            {
                "base_date": base_date,
                "base_time": base_time,
                "nx": nx,
                "ny": ny,
            },
        )
        try:
            items = body["items"]["item"]
        except (KeyError, TypeError) as exc:
            raise KmaParseError("KMA response did not contain items.item") from exc
        if isinstance(items, Mapping):
            return [items]
        if not isinstance(items, list):
            raise KmaParseError("KMA response items.item was not a list")
        return items

    def _request(
        self,
        endpoint: str | KmaEndpoint,
        params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        request_params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
        }
        request_params.update(params)

        try:
            response = self.session.get(
                f"{self.base_url}/{enum_value(endpoint)}",
                params=request_params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(f"KMA server returned HTTP {status}") from exc
            raise KmaRequestError(f"KMA request failed with HTTP {status}") from exc
        except RequestException as exc:
            raise KmaRequestError("KMA request failed") from exc

        try:
            payload = response.json()
            envelope = payload["response"]
            header = envelope["header"]
            body = envelope.get("body", {})
        except (ValueError, KeyError, TypeError) as exc:
            raise KmaParseError("KMA response was not valid JSON in the expected shape") from exc

        code = str(header.get("resultCode", ""))
        message = str(header.get("resultMsg", ""))
        if code != "00":
            _raise_for_result_code(code, message)
        if not isinstance(body, Mapping):
            raise KmaParseError("KMA response body was not an object")
        return body


def _forecast_item(item: Mapping[str, Any], endpoint: str | KmaEndpoint) -> ForecastItem:
    try:
        category = coerce_category(item["category"])
        value = item.get("fcstValue")
        nx = int(item["nx"])
        ny = int(item["ny"])
        validate_grid(nx, ny)
        return ForecastItem(
            base_at=parse_kma_datetime(str(item["baseDate"]), str(item["baseTime"])),
            forecast_at=parse_kma_datetime(str(item["fcstDate"]), str(item["fcstTime"])),
            nx=nx,
            ny=ny,
            category=category,
            value=normalize_value(category, value),
            label=label_for(category, value, endpoint=endpoint),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(f"Malformed KMA forecast item: {item!r}") from exc


def _raise_for_result_code(code: str, message: str) -> None:
    text = f"KMA API returned {code}: {message}"
    if code in {"20", "30", "31"}:
        raise KmaAuthError(text)
    if code in {"04", "99"}:
        raise KmaServerError(text)
    raise KmaRequestError(text)


def _float_or_none(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _int_or_none(value: object) -> Optional[int]:
    number = _float_or_none(value)
    if number is None:
        return None
    return int(number)

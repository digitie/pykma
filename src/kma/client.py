"""기상청 단기예보 공개 API 클라이언트."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from ._credentials import DATA_GOKR_ENV_NAMES, first_env_value, normalize_api_key
from ._http import async_get_with_retries, build_async_client, build_session, get_with_retries
from ._parsing import float_or_none as _float_or_none
from ._parsing import int_or_none as _int_or_none
from .codes import label_for, normalize_value, parse_amount
from .enums import KmaEndpoint, WeatherCategory, coerce_category, enum_value
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .grid import validate_grid
from .locations import LocationInput, normalize_location
from .metadata import ResponseMetadata, make_response_metadata, redact_credentials_in_text
from .models import ForecastItem, WeatherSnapshot
from .time_utils import (
    as_kst,
    latest_ultra_srt_fcst_base,
    latest_ultra_srt_ncst_base,
    latest_vilage_base,
    parse_kma_datetime,
)

DEFAULT_BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
SERVICE_NAME = "VilageFcstInfoService_2.0"


@dataclass(frozen=True)
class _KmaBody:
    body: Mapping[str, Any]
    metadata: ResponseMetadata


@dataclass(frozen=True)
class _FetchedItems:
    items: list[Mapping[str, Any]]
    metadata: ResponseMetadata


class KmaClient:
    """기상청 `VilageFcstInfoService_2.0` endpoint 클라이언트."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: str | None = None,
        session: Any | None = None,
        async_session: Any | None = None,
    ) -> None:
        self.service_key = normalize_api_key(service_key, field_name="service_key")
        self.timeout = timeout
        self.retries = retries
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.session = session or build_session(retries)
        self._owns_session = session is None
        self._async_session = async_session
        self._owns_async_session = async_session is None
        self.forecast: ForecastService = ForecastService(self)
        self.closed = False

    @classmethod
    def from_env(cls, name: str = "DATA_GO_KR_SERVICE_KEY", **kwargs: Any) -> KmaClient:
        names = (
            DATA_GOKR_ENV_NAMES
            if name == "DATA_GO_KR_SERVICE_KEY"
            else (name, *DATA_GOKR_ENV_NAMES)
        )
        service_key = first_env_value(names)
        return cls(service_key=service_key, **kwargs)

    @classmethod
    def aio(cls, service_key: str, **kwargs: Any) -> AsyncKmaClient:
        """Create a client intended for async use."""

        return AsyncKmaClient(service_key=service_key, **kwargs)

    @classmethod
    def aio_from_env(cls, name: str = "DATA_GO_KR_SERVICE_KEY", **kwargs: Any) -> AsyncKmaClient:
        """Create an async-capable client from environment credentials."""

        names = (
            DATA_GOKR_ENV_NAMES
            if name == "DATA_GO_KR_SERVICE_KEY"
            else (name, *DATA_GOKR_ENV_NAMES)
        )
        service_key = first_env_value(names)
        return AsyncKmaClient(service_key=service_key, **kwargs)

    def close(self) -> None:
        close = getattr(self.session, "close", None)
        if self._owns_session and close is not None:
            close()
        self.closed = True

    async def aclose(self) -> None:
        if self._async_session is None or not self._owns_async_session:
            return
        aclose = getattr(self._async_session, "aclose", None)
        close = getattr(self._async_session, "close", None)
        if aclose is not None:
            await aclose()
        elif close is not None:
            close()

    def __enter__(self) -> KmaClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    async def __aenter__(self) -> KmaClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    def now(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> WeatherSnapshot:
        """초단기실황 관측값을 조회합니다.

        `when`을 생략하면 `getUltraSrtNcst`의 최신 조회 가능 KST 기준시각을
        자동으로 선택합니다.
        """

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_ncst_base(when)
        fetched = self._fetch_items(
            KmaEndpoint.ULTRA_SRT_NCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        items = fetched.items
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
            metadata=fetched.metadata,
        )

    async def anow(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> WeatherSnapshot:
        """Asynchronously fetch `getUltraSrtNcst` observations."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_ncst_base(when)
        fetched = await self._afetch_items(
            KmaEndpoint.ULTRA_SRT_NCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        items = fetched.items
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
            metadata=fetched.metadata,
        )

    def forecast_short(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        """`getUltraSrtFcst` 초단기예보 항목을 조회합니다."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_fcst_base(when)
        fetched = self._fetch_items(
            KmaEndpoint.ULTRA_SRT_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [
            _forecast_item(item, KmaEndpoint.ULTRA_SRT_FCST, metadata=fetched.metadata)
            for item in fetched.items
        ]

    async def aforecast_short(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        """Asynchronously fetch `getUltraSrtFcst` forecast items."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_ultra_srt_fcst_base(when)
        fetched = await self._afetch_items(
            KmaEndpoint.ULTRA_SRT_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [
            _forecast_item(item, KmaEndpoint.ULTRA_SRT_FCST, metadata=fetched.metadata)
            for item in fetched.items
        ]

    def _forecast_vilage(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        """`getVilageFcst` 단기예보 항목을 조회합니다."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_vilage_base(when)
        fetched = self._fetch_items(
            KmaEndpoint.VILAGE_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [
            _forecast_item(item, KmaEndpoint.VILAGE_FCST, metadata=fetched.metadata)
            for item in fetched.items
        ]

    async def aforecast(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        """Asynchronously fetch `getVilageFcst` forecast items."""

        grid_x, grid_y = self._coordinates(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
        )
        base_date, base_time = latest_vilage_base(when)
        fetched = await self._afetch_items(
            KmaEndpoint.VILAGE_FCST,
            base_date=base_date,
            base_time=base_time,
            nx=grid_x,
            ny=grid_y,
        )
        return [
            _forecast_item(item, KmaEndpoint.VILAGE_FCST, metadata=fetched.metadata)
            for item in fetched.items
        ]

    def version(self, ftype: str, when: datetime) -> Mapping[str, Any]:
        """`getFcstVersion` 예보 버전 metadata를 조회합니다."""

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

    async def aversion(self, ftype: str, when: datetime) -> Mapping[str, Any]:
        """Asynchronously fetch `getFcstVersion` metadata."""

        when_kst = as_kst(when)
        base_date = when_kst.strftime("%Y%m%d")
        base_time = when_kst.strftime("%H%M")
        return await self._arequest(
            KmaEndpoint.FCST_VERSION,
            {
                "ftype": ftype,
                "basedatetime": f"{base_date}{base_time}",
            },
        )

    def _coordinates(
        self,
        *,
        location: LocationInput | None,
        lat: float | None,
        lon: float | None,
        nx: int | None,
        ny: int | None,
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
    ) -> _FetchedItems:
        response = self._request_with_metadata(
            endpoint,
            {
                "base_date": base_date,
                "base_time": base_time,
                "nx": nx,
                "ny": ny,
            },
        )
        try:
            items = response.body["items"]["item"]
        except (KeyError, TypeError) as exc:
            raise KmaParseError(
                "KMA response did not contain items.item",
                provider="data.go.kr",
                endpoint=enum_value(endpoint),
                failure_kind="parse",
                retryable=False,
            ) from exc
        if isinstance(items, Mapping):
            return _FetchedItems([items], response.metadata)
        if not isinstance(items, list):
            raise KmaParseError(
                "KMA response items.item was not a list",
                provider="data.go.kr",
                endpoint=enum_value(endpoint),
                failure_kind="parse",
                retryable=False,
            )
        return _FetchedItems(items, response.metadata)

    async def _afetch_items(
        self,
        endpoint: str | KmaEndpoint,
        *,
        base_date: str,
        base_time: str,
        nx: int,
        ny: int,
    ) -> _FetchedItems:
        response = await self._arequest_with_metadata(
            endpoint,
            {
                "base_date": base_date,
                "base_time": base_time,
                "nx": nx,
                "ny": ny,
            },
        )
        try:
            items = response.body["items"]["item"]
        except (KeyError, TypeError) as exc:
            raise KmaParseError(
                "KMA response did not contain items.item",
                provider="data.go.kr",
                endpoint=enum_value(endpoint),
                failure_kind="parse",
                retryable=False,
            ) from exc
        if isinstance(items, Mapping):
            return _FetchedItems([items], response.metadata)
        if not isinstance(items, list):
            raise KmaParseError(
                "KMA response items.item was not a list",
                provider="data.go.kr",
                endpoint=enum_value(endpoint),
                failure_kind="parse",
                retryable=False,
            )
        return _FetchedItems(items, response.metadata)

    def _request(
        self,
        endpoint: str | KmaEndpoint,
        params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return self._request_with_metadata(endpoint, params).body

    async def _arequest(
        self,
        endpoint: str | KmaEndpoint,
        params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return (await self._arequest_with_metadata(endpoint, params)).body

    def _request_with_metadata(
        self,
        endpoint: str | KmaEndpoint,
        params: Mapping[str, Any],
    ) -> _KmaBody:
        endpoint_name = enum_value(endpoint)
        request_params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
        }
        request_params.update(params)
        metadata = make_response_metadata(
            provider="data.go.kr",
            service_name=SERVICE_NAME,
            endpoint=endpoint_name,
            request_params=request_params,
            base_date=str(request_params.get("base_date"))
            if request_params.get("base_date") is not None
            else None,
            base_time=str(request_params.get("base_time"))
            if request_params.get("base_time") is not None
            else None,
        )

        try:
            response = get_with_retries(
                self.session,
                f"{self.base_url}/{endpoint_name}",
                params=request_params,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(
                    f"KMA server returned HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="server",
                    retryable=True,
                ) from None
            if status in {401, 403}:
                raise KmaAuthError(
                    f"KMA request failed with HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="auth",
                    retryable=False,
                ) from None
            if status == 429:
                raise KmaRequestError(
                    "KMA request failed with HTTP 429",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="rate_limit",
                    retryable=True,
                ) from None
            raise KmaRequestError(
                f"KMA request failed with HTTP {status}",
                provider="data.go.kr",
                endpoint=endpoint_name,
                status_code=status,
                failure_kind="request",
                retryable=False,
            ) from None
        except httpx.RequestError:
            raise KmaRequestError(
                "KMA request failed",
                provider="data.go.kr",
                endpoint=endpoint_name,
                failure_kind="network",
                retryable=True,
            ) from None

        return _parse_kma_body(response, endpoint_name, metadata)

    async def _arequest_with_metadata(
        self,
        endpoint: str | KmaEndpoint,
        params: Mapping[str, Any],
    ) -> _KmaBody:
        endpoint_name = enum_value(endpoint)
        request_params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
        }
        request_params.update(params)
        metadata = make_response_metadata(
            provider="data.go.kr",
            service_name=SERVICE_NAME,
            endpoint=endpoint_name,
            request_params=request_params,
            base_date=str(request_params.get("base_date"))
            if request_params.get("base_date") is not None
            else None,
            base_time=str(request_params.get("base_time"))
            if request_params.get("base_time") is not None
            else None,
        )

        try:
            response = await async_get_with_retries(
                self._get_async_session(),
                f"{self.base_url}/{endpoint_name}",
                params=request_params,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(
                    f"KMA server returned HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="server",
                    retryable=True,
                ) from None
            if status in {401, 403}:
                raise KmaAuthError(
                    f"KMA request failed with HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="auth",
                    retryable=False,
                ) from None
            if status == 429:
                raise KmaRequestError(
                    "KMA request failed with HTTP 429",
                    provider="data.go.kr",
                    endpoint=endpoint_name,
                    status_code=status,
                    failure_kind="rate_limit",
                    retryable=True,
                ) from None
            raise KmaRequestError(
                f"KMA request failed with HTTP {status}",
                provider="data.go.kr",
                endpoint=endpoint_name,
                status_code=status,
                failure_kind="request",
                retryable=False,
            ) from None
        except httpx.RequestError:
            raise KmaRequestError(
                "KMA request failed",
                provider="data.go.kr",
                endpoint=endpoint_name,
                failure_kind="network",
                retryable=True,
            ) from None

        return _parse_kma_body(response, endpoint_name, metadata)

    def _get_async_session(self) -> Any:
        if self._async_session is None:
            self._async_session = build_async_client()
        return self._async_session


class ForecastService:
    """Service facade for KMA short-term forecast endpoints."""

    def __init__(self, client: KmaClient) -> None:
        self._client = client

    def __call__(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return self.vilage(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    def now(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> WeatherSnapshot:
        return KmaClient.now(
            self._client,
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    def short(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return self._client.forecast_short(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    def vilage(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return self._client._forecast_vilage(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    def version(self, ftype: str, when: datetime) -> Mapping[str, Any]:
        return self._client.version(ftype, when)


class AsyncForecastService:
    """Async service facade for KMA short-term forecast endpoints."""

    def __init__(self, client: KmaClient) -> None:
        self._client = client

    async def __call__(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return await self.vilage(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    async def now(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> WeatherSnapshot:
        return await self._client.anow(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    async def short(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return await self._client.aforecast_short(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    async def vilage(
        self,
        *,
        location: LocationInput | None = None,
        lat: float | None = None,
        lon: float | None = None,
        nx: int | None = None,
        ny: int | None = None,
        when: datetime | None = None,
    ) -> list[ForecastItem]:
        return await self._client.aforecast(
            location=location,
            lat=lat,
            lon=lon,
            nx=nx,
            ny=ny,
            when=when,
        )

    async def version(self, ftype: str, when: datetime) -> Mapping[str, Any]:
        return await self._client.aversion(ftype, when)


class AsyncKmaClient:
    """Asynchronous facade for KMA public weather APIs."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: str | None = None,
        async_session: Any | None = None,
    ) -> None:
        self._client = KmaClient(
            service_key,
            timeout=timeout,
            retries=retries,
            base_url=base_url,
            async_session=async_session,
        )
        self.service_key = self._client.service_key
        self.config = {
            "base_url": self._client.base_url,
            "timeout": self._client.timeout,
            "retries": self._client.retries,
        }
        self.forecast = AsyncForecastService(self._client)
        self.closed = False

    @classmethod
    def from_env(cls, name: str = "DATA_GO_KR_SERVICE_KEY", **kwargs: Any) -> AsyncKmaClient:
        names = (
            DATA_GOKR_ENV_NAMES
            if name == "DATA_GO_KR_SERVICE_KEY"
            else (name, *DATA_GOKR_ENV_NAMES)
        )
        service_key = first_env_value(names)
        return cls(service_key=service_key, **kwargs)

    async def __aenter__(self) -> AsyncKmaClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()
        self._client.close()
        self.closed = True


def _parse_kma_body(response: Any, endpoint_name: str, metadata: ResponseMetadata) -> _KmaBody:
    try:
        payload = response.json()
        envelope = payload["response"]
        header = envelope["header"]
        body = envelope.get("body", {})
    except (ValueError, KeyError, TypeError) as exc:
        raise KmaParseError(
            "KMA response was not valid JSON in the expected shape",
            provider="data.go.kr",
            endpoint=endpoint_name,
            status_code=response.status_code,
            failure_kind="parse",
            retryable=False,
        ) from exc

    code = str(header.get("resultCode", ""))
    message = str(header.get("resultMsg", ""))
    if code != "00":
        _raise_for_result_code(code, message, endpoint=endpoint_name)
    if not isinstance(body, Mapping):
        raise KmaParseError(
            "KMA response body was not an object",
            provider="data.go.kr",
            endpoint=endpoint_name,
            status_code=response.status_code,
            failure_kind="parse",
            retryable=False,
        )
    return _KmaBody(body, metadata)


def _forecast_item(
    item: Mapping[str, Any],
    endpoint: str | KmaEndpoint,
    *,
    metadata: ResponseMetadata | None = None,
) -> ForecastItem:
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
            raw=dict(item),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed KMA forecast item: {item!r}",
            provider="data.go.kr",
            endpoint=enum_value(endpoint),
            failure_kind="parse",
            retryable=False,
        ) from exc


def _raise_for_result_code(code: str, message: str, *, endpoint: str) -> None:
    text = f"KMA API returned {code}: {redact_credentials_in_text(message)}"
    if code in {"20", "30", "31"}:
        raise KmaAuthError(
            text,
            provider="data.go.kr",
            endpoint=endpoint,
            result_code=code,
            failure_kind="auth",
            retryable=False,
        )
    if code in {"04", "99"}:
        raise KmaServerError(
            text,
            provider="data.go.kr",
            endpoint=endpoint,
            result_code=code,
            failure_kind="server",
            retryable=True,
        )
    if code == "22":
        raise KmaRequestError(
            text,
            provider="data.go.kr",
            endpoint=endpoint,
            result_code=code,
            failure_kind="quota",
            retryable=True,
        )
    raise KmaRequestError(
        text,
        provider="data.go.kr",
        endpoint=endpoint,
        result_code=code,
        failure_kind="request",
        retryable=False,
    )



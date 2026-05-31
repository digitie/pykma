"""data.go.kr gateway로 제공되는 기상청 API 범용 클라이언트."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

from ._credentials import DATA_GOKR_ENV_NAMES, first_env_value, normalize_api_key
from ._http import (
    async_get_with_retries,
    build_async_client,
    build_session,
    get_with_retries,
    raise_for_kma_http_error,
    raise_for_kma_network_error,
)
from ._parsing import float_or_none as _float_or_none
from ._parsing import int_or_none as _int_or_none
from ._parsing import str_or_none as _str_or_none
from .catalog import ApiCatalogEntry, api_catalog
from .codes import label_for, normalize_value
from .datagokr_catalog import (
    KMA_DATA_GOKR_DATASETS,
    KMA_DATA_GOKR_DATASETS_BY_ID,
    DataGoKrDatasetSpec,
)
from .enums import coerce_category
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .metadata import ResponseMetadata, make_response_metadata, redact_credentials_in_text
from .models import (
    BeachForecastItem,
    BeachSunTime,
    BeachTideItem,
    BeachWaterTemperature,
    BeachWaveHeight,
    DataGoKrItem,
    MidForecastItem,
)
from .pagination import has_next_page as _has_next_page
from .pagination import iter_pages as _iter_pages
from .time_utils import (
    KST,
    as_kst,
    latest_mid_fcst_time,
    latest_ultra_srt_fcst_base,
    latest_vilage_base,
    parse_kma_datetime,
)

DATA_GOKR_BASE_URL = "http://apis.data.go.kr/1360000"
MID_FCST_SERVICE = "MidFcstInfoService"
ASOS_DAILY_SERVICE = "AsosDalyInfoService"
ASOS_HOURLY_SERVICE = "AsosHourlyInfoService"
WTHR_WRN_SERVICE = "WthrWrnInfoService"
VILAGE_FCST_MSG_SERVICE = "VilageFcstMsgService"
TOUR_STN_SERVICE = "TourStnInfoService1"
LIVING_WTHR_IDX_SERVICE = "LivingWthrIdxServiceV4"
EQK_INFO_SERVICE = "EqkInfoService"
BEACH_INFO_SERVICE = "BeachInfoservice"
BEACH_ULTRA_SRT_FCST = "getUltraSrtFcstBeach"
BEACH_WAVE_HEIGHT = "getWhBuoyBeach"
BEACH_TIDE_INFO = "getTideInfoBeach"
BEACH_SUN_INFO = "getSunInfoBeach"
BEACH_WATER_TEMPERATURE = "getTwBuoyBeach"
BEACH_VILAGE_FCST = "getVilageFcstBeach"


@dataclass(frozen=True)
class _DataGoKrBody:
    body: Mapping[str, Any]
    metadata: ResponseMetadata


@dataclass(frozen=True)
class _DataGoKrItems:
    items: list[Mapping[str, Any]]
    metadata: ResponseMetadata


class DataGoKrClient:
    """`apis.data.go.kr/1360000` 서비스용 기상청 공공데이터 범용 클라이언트."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: str = DATA_GOKR_BASE_URL,
        service_key_param: str = "serviceKey",
        session: Any | None = None,
        async_session: Any | None = None,
    ) -> None:
        if not service_key_param:
            raise ValueError("service_key_param is required")
        self.service_key = normalize_api_key(service_key, field_name="service_key")
        self.service_key_param = service_key_param.strip()
        self.timeout = timeout
        self.retries = retries
        self.base_url = base_url.rstrip("/")
        self.session = session or build_session(retries)
        self._owns_session = session is None
        self._async_session = async_session
        self._owns_async_session = async_session is None

    @classmethod
    def from_env(cls, name: str = "DATA_GO_KR_SERVICE_KEY", **kwargs: Any) -> DataGoKrClient:
        names = (
            DATA_GOKR_ENV_NAMES
            if name == "DATA_GO_KR_SERVICE_KEY"
            else (name, *DATA_GOKR_ENV_NAMES)
        )
        service_key = first_env_value(names)
        return cls(service_key, **kwargs)

    @classmethod
    def aio(cls, service_key: str, **kwargs: Any) -> DataGoKrClient:
        """Create a client intended for async use."""

        return cls(service_key, **kwargs)

    @classmethod
    def aio_from_env(cls, name: str = "DATA_GO_KR_SERVICE_KEY", **kwargs: Any) -> DataGoKrClient:
        """Create an async-capable client from environment credentials."""

        return cls.from_env(name=name, **kwargs)

    def close(self) -> None:
        close = getattr(self.session, "close", None)
        if self._owns_session and close is not None:
            close()

    async def aclose(self) -> None:
        if self._async_session is None or not self._owns_async_session:
            return
        aclose = getattr(self._async_session, "aclose", None)
        close = getattr(self._async_session, "close", None)
        if aclose is not None:
            await aclose()
        elif close is not None:
            close()

    def __enter__(self) -> DataGoKrClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    async def __aenter__(self) -> DataGoKrClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    def request(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> Mapping[str, Any]:
        """JSON 응답을 지원하는 data.go.kr 기상청 service operation을 호출합니다.

        `service`는 `MidFcstInfoService` 같은 path segment이고,
        `operation`은 `getMidFcst` 같은 endpoint입니다.
        """

        return self._request_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        ).body

    async def arequest(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> Mapping[str, Any]:
        """Asynchronously call a data.go.kr KMA service operation."""

        return (
            await self._arequest_with_metadata(
                service,
                operation,
                params,
                data_type=data_type,
                page_no=page_no,
                num_of_rows=num_of_rows,
            )
        ).body

    def request_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> tuple[Mapping[str, Any], ResponseMetadata]:
        """service operation을 호출하고 `(body, metadata)`를 반환합니다."""

        response = self._request_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return response.body, response.metadata

    async def arequest_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> tuple[Mapping[str, Any], ResponseMetadata]:
        """Asynchronously call a service operation and return `(body, metadata)`."""

        response = await self._arequest_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return response.body, response.metadata

    def _request_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> _DataGoKrBody:
        clean_service = service.strip("/")
        clean_operation = operation.strip("/")
        endpoint = f"{clean_service}/{clean_operation}"
        request_params: dict[str, Any] = {
            self.service_key_param: self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)
        metadata = make_response_metadata(
            provider="data.go.kr",
            service_name=clean_service,
            endpoint=endpoint,
            request_params=request_params,
            base_date=_metadata_param(request_params, "base_date", "Base_date"),
            base_time=str(request_params.get("base_time"))
            if request_params.get("base_time") is not None
            else None,
        )

        try:
            response = get_with_retries(
                self.session,
                f"{self.base_url}/{endpoint}",
                params=request_params,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            raise_for_kma_http_error(
                exc,
                provider="data.go.kr",
                endpoint=endpoint,
                label="data.go.kr",
            )
        except httpx.RequestError:
            raise_for_kma_network_error(
                provider="data.go.kr",
                endpoint=endpoint,
                label="data.go.kr",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise KmaParseError(
                "data.go.kr response was not JSON",
                provider="data.go.kr",
                endpoint=endpoint,
                status_code=response.status_code,
                failure_kind="parse",
                retryable=False,
            ) from exc
        return _DataGoKrBody(
            _unwrap_data_gokr_payload(payload, endpoint=endpoint, status_code=response.status_code),
            metadata,
        )

    async def _arequest_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> _DataGoKrBody:
        clean_service = service.strip("/")
        clean_operation = operation.strip("/")
        endpoint = f"{clean_service}/{clean_operation}"
        request_params: dict[str, Any] = {
            self.service_key_param: self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)
        metadata = make_response_metadata(
            provider="data.go.kr",
            service_name=clean_service,
            endpoint=endpoint,
            request_params=request_params,
            base_date=_metadata_param(request_params, "base_date", "Base_date"),
            base_time=str(request_params.get("base_time"))
            if request_params.get("base_time") is not None
            else None,
        )

        try:
            response = await async_get_with_retries(
                self._get_async_session(),
                f"{self.base_url}/{endpoint}",
                params=request_params,
                timeout=self.timeout,
                retries=self.retries,
            )
        except httpx.HTTPStatusError as exc:
            raise_for_kma_http_error(
                exc,
                provider="data.go.kr",
                endpoint=endpoint,
                label="data.go.kr",
            )
        except httpx.RequestError:
            raise_for_kma_network_error(
                provider="data.go.kr",
                endpoint=endpoint,
                label="data.go.kr",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise KmaParseError(
                "data.go.kr response was not JSON",
                provider="data.go.kr",
                endpoint=endpoint,
                status_code=response.status_code,
                failure_kind="parse",
                retryable=False,
            ) from exc
        return _DataGoKrBody(
            _unwrap_data_gokr_payload(payload, endpoint=endpoint, status_code=response.status_code),
            metadata,
        )

    def items(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Mapping[str, Any]]:
        """operation을 호출하고 `response.body.items.item`을 list로 반환합니다."""

        body = self.request(service, operation, params, **kwargs)
        return _items_from_body(body, endpoint=f"{service.strip('/')}/{operation.strip('/')}")

    async def aitems(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Mapping[str, Any]]:
        """Asynchronously return `response.body.items.item` as a list."""

        body = await self.arequest(service, operation, params, **kwargs)
        return _items_from_body(body, endpoint=f"{service.strip('/')}/{operation.strip('/')}")

    def datasets(self) -> tuple[DataGoKrDatasetSpec, ...]:
        """공공데이터포털의 기상청 data.go.kr OpenAPI dataset 목록을 반환합니다."""

        return KMA_DATA_GOKR_DATASETS

    def api_catalog(
        self,
        *,
        gateway: str | None = None,
        dataset_id: str | int | None = None,
    ) -> tuple[ApiCatalogEntry, ...]:
        """UI/디버깅용으로 펼친 기상청 API 카탈로그를 반환합니다."""

        return api_catalog(gateway=gateway, dataset_id=dataset_id)

    def dataset(self, dataset_id: str | int) -> DataGoKrDatasetSpec:
        """공공데이터포털 dataset id로 기상청 data.go.kr dataset 명세를 반환합니다."""

        clean_id = str(dataset_id)
        try:
            return KMA_DATA_GOKR_DATASETS_BY_ID[clean_id]
        except KeyError:
            raise ValueError(f"unknown KMA data.go.kr dataset_id: {clean_id}") from None

    def request_dataset(
        self,
        dataset_id: str | int,
        params: Mapping[str, Any] | None = None,
        *,
        operation: str | None = None,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> Mapping[str, Any]:
        """공공데이터포털 dataset id로 기상청 data.go.kr dataset을 호출합니다."""

        _, service, selected_operation = self._dataset_service_operation(dataset_id, operation)
        return self.request(
            service,
            selected_operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def dataset_items(
        self,
        dataset_id: str | int,
        params: Mapping[str, Any] | None = None,
        *,
        operation: str | None = None,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """기상청 data.go.kr dataset을 호출하고 metadata가 있는 원본 row를 반환합니다."""

        _, service, selected_operation = self._dataset_service_operation(dataset_id, operation)
        return self._raw_items(
            service,
            selected_operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    async def adataset_items(
        self,
        dataset_id: str | int,
        params: Mapping[str, Any] | None = None,
        *,
        operation: str | None = None,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """Asynchronously call a data.go.kr dataset and return metadata-bearing rows."""

        _, service, selected_operation = self._dataset_service_operation(dataset_id, operation)
        return await self._araw_items(
            service,
            selected_operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def iter_pages(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        start_page: int = 1,
        num_of_rows: int = 10,
        max_pages: int = 100,
        max_items: int | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        """명시적 안전장치와 함께 data.go.kr 페이지네이션 응답 body를 순회합니다."""

        return _iter_pages(
            lambda page_no: self.request(
                service,
                operation,
                params,
                data_type=data_type,
                page_no=page_no,
                num_of_rows=num_of_rows,
            ),
            start_page=start_page,
            max_pages=max_pages,
            max_items=max_items,
        )

    async def aiter_pages(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        start_page: int = 1,
        num_of_rows: int = 10,
        max_pages: int = 100,
        max_items: int | None = None,
    ) -> AsyncIterator[Mapping[str, Any]]:
        """Asynchronously iterate paginated data.go.kr response bodies."""

        items_seen = 0
        for offset in range(max_pages):
            page_no = start_page + offset
            body = await self.arequest(
                service,
                operation,
                params,
                data_type=data_type,
                page_no=page_no,
                num_of_rows=num_of_rows,
            )
            yield body
            items_seen += _body_item_count(body)
            if max_items is not None and items_seen >= max_items:
                return
            if not _has_next_page(body):
                return

    def mid_forecast(
        self,
        *,
        stn_id: str | int,
        tm_fc: str | datetime | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """지역을 추정하지 않고 `MidFcstInfoService/getMidFcst`를 호출합니다."""

        return self._mid_items(
            "getMidFcst",
            {"stnId": str(stn_id), "tmFc": _resolve_tm_fc(tm_fc, when=when)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def mid_land_forecast(
        self,
        *,
        reg_id: str,
        tm_fc: str | datetime | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """기상청 중기예보 `reg_id`로 `getMidLandFcst`를 호출합니다.

        `reg_id`는 단기예보 `nx`/`ny` 격자 좌표가 아닙니다.
        `kma`는 두 식별자 사이의 mapping을 추정하거나 유지하지 않습니다.
        """

        return self._mid_items(
            "getMidLandFcst",
            {"regId": reg_id, "tmFc": _resolve_tm_fc(tm_fc, when=when)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def mid_temperature_forecast(
        self,
        *,
        reg_id: str,
        tm_fc: str | datetime | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """기상청 중기예보 `reg_id`로 `getMidTa`를 호출합니다.

        `reg_id`는 단기예보 `nx`/`ny` 격자 좌표가 아닙니다.
        """

        return self._mid_items(
            "getMidTa",
            {"regId": reg_id, "tmFc": _resolve_tm_fc(tm_fc, when=when)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def mid_sea_forecast(
        self,
        *,
        reg_id: str,
        tm_fc: str | datetime | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """기상청 중기해상예보 `reg_id`로 `getMidSeaFcst`를 호출합니다."""

        return self._mid_items(
            "getMidSeaFcst",
            {"regId": reg_id, "tmFc": _resolve_tm_fc(tm_fc, when=when)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def asos_daily_weather(
        self,
        *,
        start_dt: str | date | datetime,
        end_dt: str | date | datetime,
        stn_ids: str | int | None = None,
        data_cd: str = "ASOS",
        date_cd: str = "DAY",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`AsosDalyInfoService/getWthrDataList` 일자료를 호출합니다."""

        params: dict[str, Any] = {
            "dataCd": data_cd,
            "dateCd": date_cd,
            "startDt": _format_yyyymmdd(start_dt),
            "endDt": _format_yyyymmdd(end_dt),
        }
        if stn_ids is not None:
            params["stnIds"] = str(stn_ids)
        return self._raw_items(
            ASOS_DAILY_SERVICE,
            "getWthrDataList",
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def asos_hourly_weather(
        self,
        *,
        start_dt: str | date | datetime,
        start_hh: str | int,
        end_dt: str | date | datetime,
        end_hh: str | int,
        stn_ids: str | int | None = None,
        data_cd: str = "ASOS",
        date_cd: str = "HR",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`AsosHourlyInfoService/getWthrDataList` 시간자료를 호출합니다."""

        params: dict[str, Any] = {
            "dataCd": data_cd,
            "dateCd": date_cd,
            "startDt": _format_yyyymmdd(start_dt),
            "startHh": _format_hh(start_hh),
            "endDt": _format_yyyymmdd(end_dt),
            "endHh": _format_hh(end_hh),
        }
        if stn_ids is not None:
            params["stnIds"] = str(stn_ids)
        return self._raw_items(
            ASOS_HOURLY_SERVICE,
            "getWthrDataList",
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def weather_warning(
        self,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`WthrWrnInfoService` operation을 호출합니다.

        주로 쓰는 operation에는 `getWthrWrnList`, `getWthrWrnMsg`,
        `getWthrInfoList`, `getWthrInfo`, `getWthrBrkNewsList`,
        `getWthrBrkNews`, `getWthrPwnList`, `getWthrPwn`, `getPwnCd`,
        `getPwnStatus`가 있습니다.
        """

        return self._raw_items(
            WTHR_WRN_SERVICE,
            operation,
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def weather_warning_list(
        self,
        *,
        stn_id: str | int,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`WthrWrnInfoService/getWthrWrnList`를 호출합니다."""

        return self.weather_warning(
            "getWthrWrnList",
            _date_range_params(stn_id=stn_id, from_tm_fc=from_tm_fc, to_tm_fc=to_tm_fc),
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def forecast_message(
        self,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`VilageFcstMsgService` operation을 호출합니다."""

        return self._raw_items(
            VILAGE_FCST_MSG_SERVICE,
            operation,
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def weather_situation(
        self,
        *,
        stn_id: str | int,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`VilageFcstMsgService/getWthrSituation`을 호출합니다."""

        return self.forecast_message(
            "getWthrSituation",
            {"stnId": str(stn_id)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def land_forecast_message(
        self,
        *,
        reg_id: str,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`VilageFcstMsgService/getLandFcst`를 호출합니다."""

        return self.forecast_message(
            "getLandFcst",
            {"regId": reg_id},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def sea_forecast_message(
        self,
        *,
        reg_id: str,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`VilageFcstMsgService/getSeaFcst`를 호출합니다."""

        return self.forecast_message(
            "getSeaFcst",
            {"regId": reg_id},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def beach_ultra_short_forecast(
        self,
        *,
        beach_num: str | int,
        base_date: str | date | datetime | None = None,
        base_time: str | int | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 1000,
    ) -> list[BeachForecastItem]:
        """`BeachInfoservice/getUltraSrtFcstBeach`를 호출합니다.

        `base_date`와 `base_time`을 생략하면 `KmaClient.forecast_short()`와
        같은 규칙으로 최신 조회 가능 KST 초단기예보 base time을 선택합니다.
        """

        base_date_text, base_time_text = _resolve_base_date_time(
            base_date,
            base_time,
            latest_ultra_srt_fcst_base,
            when=when,
        )
        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_ULTRA_SRT_FCST,
            {
                "base_date": base_date_text,
                "base_time": base_time_text,
                "beach_num": _format_beach_num(beach_num),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [
            _beach_forecast_item(row, BEACH_ULTRA_SRT_FCST, metadata=fetched.metadata)
            for row in fetched.items
        ]

    def beach_forecast(
        self,
        *,
        beach_num: str | int,
        base_date: str | date | datetime | None = None,
        base_time: str | int | None = None,
        when: datetime | None = None,
        page_no: int = 1,
        num_of_rows: int = 1000,
    ) -> list[BeachForecastItem]:
        """`BeachInfoservice/getVilageFcstBeach`를 호출합니다.

        `base_date`와 `base_time`을 생략하면 `KmaClient.forecast()`와
        같은 규칙으로 최신 조회 가능 KST 단기예보 base time을 선택합니다.
        """

        base_date_text, base_time_text = _resolve_base_date_time(
            base_date,
            base_time,
            latest_vilage_base,
            when=when,
        )
        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_VILAGE_FCST,
            {
                "base_date": base_date_text,
                "base_time": base_time_text,
                "beach_num": _format_beach_num(beach_num),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [
            _beach_forecast_item(row, BEACH_VILAGE_FCST, metadata=fetched.metadata)
            for row in fetched.items
        ]

    def beach_wave_height(
        self,
        *,
        beach_num: str | int,
        search_time: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[BeachWaveHeight]:
        """해수욕장 파고 조회용 `BeachInfoservice/getWhBuoyBeach`를 호출합니다."""

        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_WAVE_HEIGHT,
            {
                "beach_num": _format_beach_num(beach_num),
                "searchTime": _format_yyyymmddhhmm(search_time),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [_beach_wave_height(row, metadata=fetched.metadata) for row in fetched.items]

    def beach_tide_info(
        self,
        *,
        beach_num: str | int,
        base_date: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[BeachTideItem]:
        """해수욕장 조석 조회용 `BeachInfoservice/getTideInfoBeach`를 호출합니다."""

        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_TIDE_INFO,
            {
                "base_date": _format_yyyymmdd(base_date),
                "beach_num": _format_beach_num(beach_num),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [_beach_tide_item(row, metadata=fetched.metadata) for row in fetched.items]

    def beach_sun_info(
        self,
        *,
        beach_num: str | int,
        base_date: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[BeachSunTime]:
        """해수욕장 일출/일몰 조회용 `BeachInfoservice/getSunInfoBeach`를 호출합니다.

        upstream Swagger는 다른 해수욕장 endpoint와 달리 요청 날짜 이름을
        `Base_date`로 표기합니다.
        """

        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_SUN_INFO,
            {
                "Base_date": _format_yyyymmdd(base_date),
                "beach_num": _format_beach_num(beach_num),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [_beach_sun_time(row, metadata=fetched.metadata) for row in fetched.items]

    def beach_water_temperature(
        self,
        *,
        beach_num: str | int,
        search_time: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[BeachWaterTemperature]:
        """해수욕장 수온 조회용 `BeachInfoservice/getTwBuoyBeach`를 호출합니다."""

        fetched = self._items_with_metadata(
            BEACH_INFO_SERVICE,
            BEACH_WATER_TEMPERATURE,
            {
                "beach_num": _format_beach_num(beach_num),
                "searchTime": _format_yyyymmddhhmm(search_time),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [_beach_water_temperature(row, metadata=fetched.metadata) for row in fetched.items]

    def tour_village_forecast(
        self,
        *,
        course_id: str | int,
        current_date: str | date | datetime,
        hour: str | int,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`TourStnInfoService1/getTourStnVilageFcst1`을 호출합니다."""

        return self._raw_items(
            TOUR_STN_SERVICE,
            "getTourStnVilageFcst1",
            {
                "CURRENT_DATE": _format_yyyymmdd(current_date),
                "HOUR": _format_hh(hour),
                "COURSE_ID": str(course_id),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def city_tour_climate_index(
        self,
        *,
        city_area_id: str | int,
        current_date: str | date | datetime,
        day: str | int,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`TourStnInfoService1/getCityTourClmIdx1`을 호출합니다."""

        return self._raw_items(
            TOUR_STN_SERVICE,
            "getCityTourClmIdx1",
            {
                "CURRENT_DATE": _format_yyyymmdd(current_date),
                "DAY": str(day),
                "CITY_AREA_ID": str(city_area_id),
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def sensible_temperature_index(
        self,
        *,
        area_no: str | int,
        time: str | datetime,
        request_code: str,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`LivingWthrIdxServiceV4/getSenTaIdxV4`를 호출합니다."""

        return self._living_weather_index(
            "getSenTaIdxV4",
            area_no=area_no,
            time=time,
            request_code=request_code,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def uv_index(
        self,
        *,
        area_no: str | int,
        time: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`LivingWthrIdxServiceV4/getUVIdxV4`를 호출합니다."""

        return self._living_weather_index(
            "getUVIdxV4",
            area_no=area_no,
            time=time,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def air_diffusion_index(
        self,
        *,
        area_no: str | int,
        time: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`LivingWthrIdxServiceV4/getAirDiffusionIdxV4`를 호출합니다."""

        return self._living_weather_index(
            "getAirDiffusionIdxV4",
            area_no=area_no,
            time=time,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def earthquake_info(
        self,
        operation: str,
        *,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`EqkInfoService` operation을 호출합니다."""

        return self._raw_items(
            EQK_INFO_SERVICE,
            operation,
            {"fromTmFc": _format_yyyymmdd(from_tm_fc), "toTmFc": _format_yyyymmdd(to_tm_fc)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def earthquake_message(
        self,
        *,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`EqkInfoService/getEqkMsg`를 호출합니다."""

        return self.earthquake_info(
            "getEqkMsg",
            from_tm_fc=from_tm_fc,
            to_tm_fc=to_tm_fc,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def earthquake_message_list(
        self,
        *,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`EqkInfoService/getEqkMsgList`를 호출합니다."""

        return self.earthquake_info(
            "getEqkMsgList",
            from_tm_fc=from_tm_fc,
            to_tm_fc=to_tm_fc,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def tsunami_message(
        self,
        *,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`EqkInfoService/getTsunamiMsg`를 호출합니다."""

        return self.earthquake_info(
            "getTsunamiMsg",
            from_tm_fc=from_tm_fc,
            to_tm_fc=to_tm_fc,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def tsunami_message_list(
        self,
        *,
        from_tm_fc: str | date | datetime,
        to_tm_fc: str | date | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        """`EqkInfoService/getTsunamiMsgList`를 호출합니다."""

        return self.earthquake_info(
            "getTsunamiMsgList",
            from_tm_fc=from_tm_fc,
            to_tm_fc=to_tm_fc,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def _living_weather_index(
        self,
        operation: str,
        *,
        area_no: str | int,
        time: str | datetime,
        request_code: str | None = None,
        page_no: int,
        num_of_rows: int,
    ) -> list[DataGoKrItem]:
        params: dict[str, Any] = {
            "areaNo": str(area_no),
            "time": _format_yyyymmddhh(time),
        }
        if request_code is not None:
            params["requestCode"] = request_code
        return self._raw_items(
            LIVING_WTHR_IDX_SERVICE,
            operation,
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def _dataset_service_operation(
        self,
        dataset_id: str | int,
        operation: str | None,
    ) -> tuple[DataGoKrDatasetSpec, str, str]:
        spec = self.dataset(dataset_id)
        if spec.gateway != "datagokr" or spec.service is None:
            raise ValueError(
                f"{spec.dataset_id} is APIHub-linked; use ApiHubClient "
                "or ApiHubGeneratedClient"
            )
        if operation is None:
            if len(spec.operations) == 1:
                selected_operation = spec.operations[0]
            elif spec.operations:
                known = ", ".join(spec.operations)
                raise ValueError(
                    f"operation is required for {spec.dataset_id}; known operations: {known}"
                )
            else:
                raise ValueError(f"operation is required for {spec.dataset_id}")
        else:
            selected_operation = operation.strip("/")
            if not selected_operation:
                raise ValueError("operation is required")
        return spec, spec.service, selected_operation

    def _raw_items(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        fetched = self._items_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        clean_service = service.strip("/")
        clean_operation = operation.strip("/")
        return [
            DataGoKrItem(
                service=clean_service,
                operation=clean_operation,
                raw=dict(row),
                metadata=fetched.metadata,
            )
            for row in fetched.items
        ]

    async def _araw_items(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[DataGoKrItem]:
        fetched = await self._aitems_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        clean_service = service.strip("/")
        clean_operation = operation.strip("/")
        return [
            DataGoKrItem(
                service=clean_service,
                operation=clean_operation,
                raw=dict(row),
                metadata=fetched.metadata,
            )
            for row in fetched.items
        ]

    def _items_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> _DataGoKrItems:
        response = self._request_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        endpoint = f"{service.strip('/')}/{operation.strip('/')}"
        return _DataGoKrItems(
            _items_from_body(response.body, endpoint=endpoint),
            response.metadata,
        )

    async def _aitems_with_metadata(
        self,
        service: str,
        operation: str,
        params: Mapping[str, Any] | None = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> _DataGoKrItems:
        response = await self._arequest_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        endpoint = f"{service.strip('/')}/{operation.strip('/')}"
        return _DataGoKrItems(
            _items_from_body(response.body, endpoint=endpoint),
            response.metadata,
        )

    def _mid_items(
        self,
        operation: str,
        params: Mapping[str, Any],
        *,
        page_no: int,
        num_of_rows: int,
    ) -> list[MidForecastItem]:
        fetched = self._items_with_metadata(
            MID_FCST_SERVICE,
            operation,
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        return [_mid_forecast_item(row, operation, fetched.metadata) for row in fetched.items]

    def _get_async_session(self) -> Any:
        if self._async_session is None:
            self._async_session = build_async_client()
        return self._async_session


def _resolve_base_date_time(
    base_date: str | date | datetime | None,
    base_time: str | int | None,
    latest: Callable[[datetime | None], tuple[str, str]],
    *,
    when: datetime | None,
) -> tuple[str, str]:
    if when is not None and (base_date is not None or base_time is not None):
        raise ValueError("when cannot be combined with base_date/base_time")
    if base_date is None and base_time is None:
        return latest(when)
    if base_date is None or base_time is None:
        raise ValueError("base_date and base_time must be provided together")
    return _format_yyyymmdd(base_date), _format_hhmm(base_time)


def _format_beach_num(value: str | int) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError("beach_num is required")
    return text


def _format_yyyymmdd(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return as_kst(value).strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    if len(text) != 8 or not text.isdigit():
        raise ValueError("base_date must be YYYYMMDD")
    return text


def _format_hhmm(value: str | int) -> str:
    if isinstance(value, int):
        text = f"{value:04d}"
    else:
        text = str(value).strip()
    if len(text) != 4 or not text.isdigit():
        raise ValueError("base_time must be HHMM")
    hour = int(text[:2])
    minute = int(text[2:])
    if hour > 23 or minute > 59:
        raise ValueError("base_time must be a valid HHMM value")
    return text


def _format_hh(value: str | int) -> str:
    if isinstance(value, int):
        text = f"{value:02d}"
    else:
        text = str(value).strip()
    if len(text) != 2 or not text.isdigit():
        raise ValueError("hour must be HH")
    if int(text) > 23:
        raise ValueError("hour must be between 00 and 23")
    return text


def _format_yyyymmddhh(value: str | datetime) -> str:
    if isinstance(value, datetime):
        return as_kst(value).strftime("%Y%m%d%H")
    text = str(value).strip()
    if len(text) != 10 or not text.isdigit():
        raise ValueError("time must be YYYYMMDDHH")
    return text


def _format_yyyymmddhhmm(value: str | datetime) -> str:
    if isinstance(value, datetime):
        return as_kst(value).strftime("%Y%m%d%H%M")
    text = str(value).strip()
    if len(text) != 12 or not text.isdigit():
        raise ValueError("search_time must be YYYYMMDDHHMM")
    return text


def _date_range_params(
    *,
    stn_id: str | int,
    from_tm_fc: str | date | datetime,
    to_tm_fc: str | date | datetime,
) -> dict[str, str]:
    return {
        "stnId": str(stn_id),
        "fromTmFc": _format_yyyymmdd(from_tm_fc),
        "toTmFc": _format_yyyymmdd(to_tm_fc),
    }


def _metadata_param(params: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = params.get(name)
        if value is not None:
            return str(value)
    return None


def _beach_forecast_item(
    row: Mapping[str, Any],
    operation: str,
    *,
    metadata: ResponseMetadata | None = None,
) -> BeachForecastItem:
    try:
        category = coerce_category(row["category"])
        value = row.get("fcstValue")
        nx = _int_or_none(row.get("nx"))
        ny = _int_or_none(row.get("ny"))
        return BeachForecastItem(
            operation=operation,
            base_at=parse_kma_datetime(str(row["baseDate"]), str(row["baseTime"])),
            forecast_at=parse_kma_datetime(str(row["fcstDate"]), str(row["fcstTime"])),
            beach_num=_required_text(row["beachNum"], "beachNum"),
            category=category,
            value=normalize_value(category, value),
            label=label_for(category, value, endpoint=operation),
            nx=nx,
            ny=ny,
            raw=dict(row),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed beach forecast item: {row!r}",
            provider="data.go.kr",
            endpoint=f"{BEACH_INFO_SERVICE}/{operation}",
            failure_kind="parse",
            retryable=False,
        ) from exc


def _beach_wave_height(
    row: Mapping[str, Any],
    *,
    metadata: ResponseMetadata | None = None,
) -> BeachWaveHeight:
    try:
        return BeachWaveHeight(
            observed_at=_parse_yyyymmddhhmm(row["tm"], field="tm"),
            beach_num=_required_text(row["beachNum"], "beachNum"),
            wave_height=_float_or_none(row.get("wh")),
            raw=dict(row),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed beach wave-height item: {row!r}",
            provider="data.go.kr",
            endpoint=f"{BEACH_INFO_SERVICE}/{BEACH_WAVE_HEIGHT}",
            failure_kind="parse",
            retryable=False,
        ) from exc


def _beach_water_temperature(
    row: Mapping[str, Any],
    *,
    metadata: ResponseMetadata | None = None,
) -> BeachWaterTemperature:
    try:
        return BeachWaterTemperature(
            observed_at=_parse_yyyymmddhhmm(row["tm"], field="tm"),
            beach_num=_required_text(row["beachNum"], "beachNum"),
            water_temperature=_float_or_none(row.get("tw")),
            raw=dict(row),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed beach water-temperature item: {row!r}",
            provider="data.go.kr",
            endpoint=f"{BEACH_INFO_SERVICE}/{BEACH_WATER_TEMPERATURE}",
            failure_kind="parse",
            retryable=False,
        ) from exc


def _beach_tide_item(
    row: Mapping[str, Any],
    *,
    metadata: ResponseMetadata | None = None,
) -> BeachTideItem:
    try:
        return BeachTideItem(
            base_date=_required_text(row["baseDate"], "baseDate"),
            beach_num=_required_text(row["beachNum"], "beachNum"),
            station_name=_str_or_none(row.get("tiStnld")),
            tide_time=_str_or_none(row.get("tiTime")),
            tide_type=_str_or_none(row.get("tiType")),
            tide_level=_float_or_none(row.get("tilevel")),
            raw=dict(row),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed beach tide item: {row!r}",
            provider="data.go.kr",
            endpoint=f"{BEACH_INFO_SERVICE}/{BEACH_TIDE_INFO}",
            failure_kind="parse",
            retryable=False,
        ) from exc


def _beach_sun_time(
    row: Mapping[str, Any],
    *,
    metadata: ResponseMetadata | None = None,
) -> BeachSunTime:
    try:
        return BeachSunTime(
            base_date=_required_text(row["baseDate"], "baseDate"),
            beach_num=_required_text(row["beachNum"], "beachNum"),
            sunrise=_str_or_none(row.get("sunrise")),
            sunset=_str_or_none(row.get("sunset")),
            raw=dict(row),
            metadata=metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KmaParseError(
            f"Malformed beach sun-time item: {row!r}",
            provider="data.go.kr",
            endpoint=f"{BEACH_INFO_SERVICE}/{BEACH_SUN_INFO}",
            failure_kind="parse",
            retryable=False,
        ) from exc


def _parse_yyyymmddhhmm(value: object, *, field: str) -> datetime:
    text = _required_text(value, field)
    if len(text) != 12 or not text.isdigit():
        raise ValueError(f"{field} must be YYYYMMDDHHMM")
    return datetime.strptime(text, "%Y%m%d%H%M").replace(tzinfo=KST)


def _required_text(value: object, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text




def _items_from_body(body: Mapping[str, Any], *, endpoint: str) -> list[Mapping[str, Any]]:
    try:
        raw_items = body["items"]["item"]
    except (KeyError, TypeError) as exc:
        raise KmaParseError(
            "data.go.kr response did not contain body.items.item",
            provider="data.go.kr",
            endpoint=endpoint,
            failure_kind="parse",
            retryable=False,
        ) from exc
    if isinstance(raw_items, Mapping):
        return [raw_items]
    if isinstance(raw_items, list):
        return raw_items
    raise KmaParseError(
        "data.go.kr response body.items.item was not a list or object",
        provider="data.go.kr",
        endpoint=endpoint,
        failure_kind="parse",
        retryable=False,
    )


def _body_item_count(body: Mapping[str, Any]) -> int:
    items = body.get("items")
    if not isinstance(items, Mapping):
        return 0
    raw = items.get("item")
    if isinstance(raw, list):
        return len(raw)
    if isinstance(raw, Mapping):
        return 1
    return 0


def _mid_forecast_item(
    row: Mapping[str, Any],
    operation: str,
    metadata: ResponseMetadata,
) -> MidForecastItem:
    return MidForecastItem(
        operation=operation,
        tm_fc=_str_or_none(row.get("tmFc")),
        reg_id=_str_or_none(row.get("regId")),
        stn_id=_str_or_none(row.get("stnId")),
        raw=dict(row),
        metadata=metadata,
    )


def _format_tm_fc(value: str | datetime) -> str:
    if isinstance(value, datetime):
        return as_kst(value).strftime("%Y%m%d%H%M")
    text = str(value).strip()
    if len(text) != 12 or not text.isdigit():
        raise ValueError("tm_fc must be YYYYMMDDHHMM")
    return text


def _resolve_tm_fc(value: str | datetime | None, *, when: datetime | None) -> str:
    if value is not None and when is not None:
        raise ValueError("when cannot be combined with tm_fc")
    if value is None:
        return latest_mid_fcst_time(when)
    return _format_tm_fc(value)




def _unwrap_data_gokr_payload(
    payload: Mapping[str, Any],
    *,
    endpoint: str,
    status_code: int,
) -> Mapping[str, Any]:
    try:
        envelope = payload["response"]
        header = envelope["header"]
        body = envelope.get("body", {})
    except (KeyError, TypeError) as exc:
        raise KmaParseError(
            "data.go.kr response was not in the expected response/header/body shape",
            provider="data.go.kr",
            endpoint=endpoint,
            status_code=status_code,
            failure_kind="parse",
            retryable=False,
        ) from exc

    code = str(header.get("resultCode", ""))
    message = str(header.get("resultMsg", ""))
    if code != "00":
        _raise_for_data_gokr_result_code(code, message, endpoint=endpoint)
    if not isinstance(body, Mapping):
        raise KmaParseError(
            "data.go.kr response body was not an object",
            provider="data.go.kr",
            endpoint=endpoint,
            status_code=status_code,
            failure_kind="parse",
            retryable=False,
        )
    return body


def _raise_for_data_gokr_result_code(code: str, message: str, *, endpoint: str) -> None:
    text = f"data.go.kr API returned {code}: {redact_credentials_in_text(message)}"
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

"""Generic client for KMA APIs served through data.go.kr."""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ._http import build_session
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from .metadata import ResponseMetadata, make_response_metadata, redact_credentials_in_text
from .models import MidForecastItem
from .pagination import iter_pages as _iter_pages

try:
    import requests
    from requests import HTTPError, RequestException
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore[assignment]
    HTTPError = ()  # type: ignore[assignment,misc]
    RequestException = ()  # type: ignore[assignment,misc]

DATA_GOKR_BASE_URL = "http://apis.data.go.kr/1360000"
MID_FCST_SERVICE = "MidFcstInfoService"


@dataclass(frozen=True)
class _DataGoKrBody:
    body: Mapping[str, Any]
    metadata: ResponseMetadata


class DataGoKrClient:
    """Generic KMA public-data client for `apis.data.go.kr/1360000` services."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10,
        retries: int = 3,
        base_url: str = DATA_GOKR_BASE_URL,
        service_key_param: str = "serviceKey",
        session: Any | None = None,
    ) -> None:
        if not service_key:
            raise ValueError("service_key is required")
        if not service_key_param:
            raise ValueError("service_key_param is required")
        self.service_key = service_key
        self.service_key_param = service_key_param
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")
        self.session = session or build_session(retries)

    @classmethod
    def from_env(cls, name: str = "KMA_SERVICE_KEY", **kwargs: Any) -> DataGoKrClient:
        try:
            service_key = os.environ[name]
        except KeyError as exc:
            raise ValueError(f"{name} is not set") from exc
        return cls(service_key, **kwargs)

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
        """Call any JSON-capable data.go.kr KMA service operation.

        `service` is the path segment such as `MidFcstInfoService`.
        `operation` is the endpoint such as `getMidFcst`.
        """

        return self._request_with_metadata(
            service,
            operation,
            params,
            data_type=data_type,
            page_no=page_no,
            num_of_rows=num_of_rows,
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
        """Call a service operation and return `(body, metadata)`."""

        response = self._request_with_metadata(
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
            base_date=str(request_params.get("base_date"))
            if request_params.get("base_date") is not None
            else None,
            base_time=str(request_params.get("base_time"))
            if request_params.get("base_time") is not None
            else None,
        )

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=request_params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(
                    f"data.go.kr server returned HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="server",
                    retryable=True,
                ) from None
            if status in {401, 403}:
                raise KmaAuthError(
                    f"data.go.kr request failed with HTTP {status}",
                    provider="data.go.kr",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="auth",
                    retryable=False,
                ) from None
            if status == 429:
                raise KmaRequestError(
                    "data.go.kr request failed with HTTP 429",
                    provider="data.go.kr",
                    endpoint=endpoint,
                    status_code=status,
                    failure_kind="rate_limit",
                    retryable=True,
                ) from None
            raise KmaRequestError(
                f"data.go.kr request failed with HTTP {status}",
                provider="data.go.kr",
                endpoint=endpoint,
                status_code=status,
                failure_kind="request",
                retryable=False,
            ) from None
        except RequestException:
            raise KmaRequestError(
                "data.go.kr request failed",
                provider="data.go.kr",
                endpoint=endpoint,
                failure_kind="network",
                retryable=True,
            ) from None

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
        """Call an operation and return `response.body.items.item` as a list."""

        body = self.request(service, operation, params, **kwargs)
        return _items_from_body(body, endpoint=f"{service.strip('/')}/{operation.strip('/')}")

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
        """Iterate paginated data.go.kr response bodies with explicit guards."""

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

    def mid_forecast(
        self,
        *,
        stn_id: str | int,
        tm_fc: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """Call `MidFcstInfoService/getMidFcst` without guessing regions."""

        return self._mid_items(
            "getMidFcst",
            {"stnId": str(stn_id), "tmFc": _format_tm_fc(tm_fc)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def mid_land_forecast(
        self,
        *,
        reg_id: str,
        tm_fc: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """Call `getMidLandFcst` for a KMA mid-term `reg_id`.

        `reg_id` is not a short-term forecast `nx`/`ny` grid coordinate.
        pykma does not infer or maintain mappings between those identifiers.
        """

        return self._mid_items(
            "getMidLandFcst",
            {"regId": reg_id, "tmFc": _format_tm_fc(tm_fc)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def mid_temperature_forecast(
        self,
        *,
        reg_id: str,
        tm_fc: str | datetime,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> list[MidForecastItem]:
        """Call `getMidTa` for a KMA mid-term `reg_id`.

        `reg_id` is not a short-term forecast `nx`/`ny` grid coordinate.
        """

        return self._mid_items(
            "getMidTa",
            {"regId": reg_id, "tmFc": _format_tm_fc(tm_fc)},
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    def _mid_items(
        self,
        operation: str,
        params: Mapping[str, Any],
        *,
        page_no: int,
        num_of_rows: int,
    ) -> list[MidForecastItem]:
        response = self._request_with_metadata(
            MID_FCST_SERVICE,
            operation,
            params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )
        rows = _items_from_body(response.body, endpoint=f"{MID_FCST_SERVICE}/{operation}")
        return [_mid_forecast_item(row, operation, response.metadata) for row in rows]


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
        return value.strftime("%Y%m%d%H%M")
    text = str(value).strip()
    if len(text) != 12 or not text.isdigit():
        raise ValueError("tm_fc must be YYYYMMDDHHMM")
    return text


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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

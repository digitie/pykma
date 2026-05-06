"""Generic client for KMA APIs served through data.go.kr."""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from ._http import build_session
from .exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError

try:
    import requests
    from requests import HTTPError, RequestException
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore[assignment]
    HTTPError = ()  # type: ignore[assignment]
    RequestException = ()  # type: ignore[assignment]

DATA_GOKR_BASE_URL = "http://apis.data.go.kr/1360000"


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
        session: Optional[Any] = None,
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
    def from_env(cls, name: str = "KMA_SERVICE_KEY", **kwargs: Any) -> "DataGoKrClient":
        try:
            service_key = os.environ[name]
        except KeyError as exc:
            raise ValueError(f"{name} is not set") from exc
        return cls(service_key, **kwargs)

    def request(
        self,
        service: str,
        operation: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> Mapping[str, Any]:
        """Call any JSON-capable data.go.kr KMA service operation.

        `service` is the path segment such as `MidFcstInfoService`.
        `operation` is the endpoint such as `getMidFcst`.
        """

        request_params: dict[str, Any] = {
            self.service_key_param: self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)

        try:
            response = self.session.get(
                f"{self.base_url}/{service.strip('/')}/{operation.strip('/')}",
                params=request_params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(f"data.go.kr server returned HTTP {status}") from exc
            raise KmaRequestError(f"data.go.kr request failed with HTTP {status}") from exc
        except RequestException as exc:
            raise KmaRequestError("data.go.kr request failed") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise KmaParseError("data.go.kr response was not JSON") from exc
        return _unwrap_data_gokr_payload(payload)

    def items(
        self,
        service: str,
        operation: str,
        params: Optional[Mapping[str, Any]] = None,
        **kwargs: Any,
    ) -> list[Mapping[str, Any]]:
        """Call an operation and return `response.body.items.item` as a list."""

        body = self.request(service, operation, params, **kwargs)
        try:
            raw_items = body["items"]["item"]
        except (KeyError, TypeError) as exc:
            raise KmaParseError("data.go.kr response did not contain body.items.item") from exc
        if isinstance(raw_items, Mapping):
            return [raw_items]
        if isinstance(raw_items, list):
            return raw_items
        raise KmaParseError("data.go.kr response body.items.item was not a list or object")


def _unwrap_data_gokr_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        envelope = payload["response"]
        header = envelope["header"]
        body = envelope.get("body", {})
    except (KeyError, TypeError) as exc:
        raise KmaParseError("data.go.kr response was not in the expected response/header/body shape") from exc

    code = str(header.get("resultCode", ""))
    message = str(header.get("resultMsg", ""))
    if code != "00":
        _raise_for_data_gokr_result_code(code, message)
    if not isinstance(body, Mapping):
        raise KmaParseError("data.go.kr response body was not an object")
    return body


def _raise_for_data_gokr_result_code(code: str, message: str) -> None:
    text = f"data.go.kr API returned {code}: {message}"
    if code in {"20", "30", "31"}:
        raise KmaAuthError(text)
    if code in {"04", "99"}:
        raise KmaServerError(text)
    raise KmaRequestError(text)

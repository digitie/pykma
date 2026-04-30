"""Generic client and discovery helpers for the KMA APIHub."""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.parse import parse_qsl, urlsplit

from ._http import build_session
from .exceptions import KmaParseError, KmaRequestError, KmaServerError

try:
    import requests
    from requests import HTTPError, RequestException
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore[assignment]
    HTTPError = ()  # type: ignore[assignment]
    RequestException = ()  # type: ignore[assignment]

APIHUB_BASE_URL = "https://apihub.kma.go.kr"
APIHUB_CATEGORY_IDS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15)

APIHUB_CATEGORIES: dict[int, str] = {
    2: "지상관측",
    3: "해양관측",
    4: "고층관측",
    5: "레이더",
    6: "위성",
    7: "지진/화산",
    8: "태풍",
    9: "수치모델",
    10: "예특보",
    11: "융합기상",
    12: "세계기상",
    13: "산업특화",
    14: "항공기상",
    15: "기후변화",
}


@dataclass(frozen=True)
class ApiHubService:
    category_id: int
    category_name: str
    service_id: int
    service_name: str


@dataclass(frozen=True)
class ApiHubEndpoint:
    path: str
    parameters: tuple[str, ...]
    sample_params: Mapping[str, str]


@dataclass(frozen=True)
class ApiHubResponse:
    url: str
    status_code: int
    content_type: str
    text: str
    content: bytes

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except ValueError as exc:
            raise KmaParseError("APIHub response was not JSON") from exc


class ApiHubClient:
    """Generic client for KMA APIHub `authKey` APIs.

    APIHub exposes many text, JSON, XML, image, and file endpoints. This client
    intentionally provides a generic path caller plus discovery helpers instead
    of pretending every endpoint has the same schema.
    """

    def __init__(
        self,
        auth_key: str,
        *,
        timeout: float = 20,
        retries: int = 3,
        base_url: str = APIHUB_BASE_URL,
        session: Optional[Any] = None,
    ) -> None:
        if not auth_key:
            raise ValueError("auth_key is required")
        self.auth_key = auth_key
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")
        self.session = session or build_session(retries)

    @classmethod
    def from_env(cls, name: str = "KMA_APIHUB_AUTH_KEY", **kwargs: Any) -> "ApiHubClient":
        auth_key = os.getenv(name) or os.getenv("KMA_APIHUB_KEY")
        if not auth_key:
            raise ValueError(f"{name} or KMA_APIHUB_KEY is not set")
        return cls(auth_key, **kwargs)

    def request_path(
        self,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
    ) -> ApiHubResponse:
        """Call any APIHub path under `/api/...` and append `authKey`."""

        clean_path = _normalize_apihub_path(path)
        request_params: dict[str, Any] = {"authKey": self.auth_key}
        if params:
            request_params.update(params)
        return self._get(clean_path, request_params)

    def open_api(
        self,
        service: str,
        operation: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        data_type: str = "JSON",
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> ApiHubResponse:
        """Call a `/api/typ02/openApi/{service}/{operation}` endpoint."""

        request_params: dict[str, Any] = {
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "dataType": data_type,
        }
        if params:
            request_params.update(params)
        return self.request_path(
            f"/api/typ02/openApi/{service.strip('/')}/{operation.strip('/')}",
            request_params,
        )

    def discover_services(
        self,
        category_ids: tuple[int, ...] = APIHUB_CATEGORY_IDS,
    ) -> list[ApiHubService]:
        """Fetch APIHub service lists for official category ids."""

        services: list[ApiHubService] = []
        for category_id in category_ids:
            response = self._portal_get("/apiList.do", {"seqApi": category_id})
            services.extend(parse_apihub_services(response.text, category_id))
        return services

    def discover_endpoints(self, category_id: int, service_id: int) -> list[ApiHubEndpoint]:
        """Fetch endpoint samples for one APIHub service page."""

        response = self._portal_get(
            "/apiList.do",
            {"seqApi": category_id, "seqApiSub": service_id},
        )
        return extract_apihub_endpoints(response.text)

    def _portal_get(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        return self._get(path, params)

    def _get(self, path: str, params: Mapping[str, Any]) -> ApiHubResponse:
        try:
            response = self.session.get(
                f"{self.base_url}/{path.lstrip('/')}",
                params=dict(params),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status and status >= 500:
                raise KmaServerError(f"APIHub server returned HTTP {status}") from exc
            raise KmaRequestError(f"APIHub request failed with HTTP {status}") from exc
        except RequestException as exc:
            raise KmaRequestError("APIHub request failed") from exc

        content_type = response.headers.get("Content-Type", "")
        return ApiHubResponse(
            url=response.url,
            status_code=response.status_code,
            content_type=content_type,
            text=response.text,
            content=response.content,
        )


def parse_apihub_services(html_text: str, category_id: int) -> list[ApiHubService]:
    """Parse APIHub's `const apiList = [...]` service list."""

    match = re.search(r"const\s+apiList\s*=\s*(\[.*?\]);", html_text, re.S)
    if not match:
        return []
    try:
        raw_services = json.loads(match.group(1))
    except ValueError as exc:
        raise KmaParseError("Could not parse APIHub apiList JSON") from exc

    category_name = APIHUB_CATEGORIES.get(category_id, str(category_id))
    services: list[ApiHubService] = []
    for raw in raw_services:
        try:
            services.append(
                ApiHubService(
                    category_id=category_id,
                    category_name=category_name,
                    service_id=int(raw["seqApi"]),
                    service_name=str(raw["nmApi"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise KmaParseError(f"Malformed APIHub service entry: {raw!r}") from exc
    return services


def extract_apihub_endpoints(html_text: str) -> list[ApiHubEndpoint]:
    """Extract generated API sample URLs from an APIHub service page."""

    endpoints: list[ApiHubEndpoint] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for raw in re.findall(r"https://apihub\.kma\.go\.kr/api/[^\s\"<>]+", html_text):
        endpoint = parse_apihub_sample_url(raw)
        key = (endpoint.path, endpoint.parameters)
        if key not in seen:
            endpoints.append(endpoint)
            seen.add(key)
    return endpoints


def parse_apihub_sample_url(raw_url: str) -> ApiHubEndpoint:
    """Parse one APIHub sample URL into path, params, and sample values."""

    cleaned = html.unescape(raw_url).replace("&amp;", "&")
    parts = urlsplit(cleaned)
    sample_params: dict[str, str] = {}
    parameters: list[str] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "authKey":
            continue
        if key not in sample_params:
            parameters.append(key)
            sample_params[key] = value
    return ApiHubEndpoint(parts.path, tuple(parameters), sample_params)


def _normalize_apihub_path(path: str) -> str:
    parts = urlsplit(path)
    clean = parts.path if parts.scheme or parts.netloc else path
    if not clean.startswith("/api/"):
        raise ValueError("APIHub path must start with /api/")
    return clean


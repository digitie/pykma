"""Python helpers for KMA public weather APIs."""

from .apihub import (
    ApiHubAttachment,
    ApiHubClient,
    ApiHubEndpoint,
    ApiHubResponse,
    ApiHubService,
)
from .apihub_endpoints import APIHUB_ATTACHMENTS, APIHUB_ENDPOINTS, ApiHubGeneratedClient
from .client import KmaClient
from .codes import label_for, parse_amount, unit_for
from .datagokr import DataGoKrClient
from .enums import (
    ForecastPrecipitationType,
    KmaEndpoint,
    ObservedPrecipitationType,
    SkyCode,
    WeatherCategory,
)
from .exceptions import (
    KmaAuthError,
    KmaError,
    KmaParseError,
    KmaRequestError,
    KmaServerError,
)
from .grid import to_grid, to_latlon
from .locations import GridPoint, LatLon, normalize_location
from .models import ForecastItem, WeatherSnapshot

__all__ = [
    "ForecastItem",
    "ApiHubAttachment",
    "ApiHubClient",
    "ApiHubEndpoint",
    "ApiHubGeneratedClient",
    "ApiHubResponse",
    "ApiHubService",
    "APIHUB_ATTACHMENTS",
    "APIHUB_ENDPOINTS",
    "DataGoKrClient",
    "ForecastPrecipitationType",
    "GridPoint",
    "KmaAuthError",
    "KmaClient",
    "KmaEndpoint",
    "KmaError",
    "KmaParseError",
    "KmaRequestError",
    "KmaServerError",
    "LatLon",
    "ObservedPrecipitationType",
    "SkyCode",
    "WeatherCategory",
    "WeatherSnapshot",
    "label_for",
    "normalize_location",
    "parse_amount",
    "to_grid",
    "to_latlon",
    "unit_for",
]

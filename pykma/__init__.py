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
from .datagokr_catalog import KMA_DATA_GOKR_DATASETS, DataGoKrDatasetSpec
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
from .expressway import ExpresswayRestAreaWeatherClient
from .grid import kma_grid_to_wgs84, to_grid, to_latlon, wgs84_to_kma_grid
from .locations import GridPoint, LatLon, normalize_location
from .metadata import ResponseMetadata, make_cache_key, sanitize_request_params
from .models import (
    BeachForecastItem,
    BeachSunTime,
    BeachTideItem,
    BeachWaterTemperature,
    BeachWaveHeight,
    DataGoKrItem,
    ForecastItem,
    MidForecastItem,
    RestAreaWeather,
    WeatherSnapshot,
)
from .pagination import has_next_page, iter_pages, next_page_no

__all__ = [
    "APIHUB_ATTACHMENTS",
    "APIHUB_ENDPOINTS",
    "ApiHubClient",
    "ApiHubAttachment",
    "ApiHubEndpoint",
    "ApiHubGeneratedClient",
    "ApiHubResponse",
    "ApiHubService",
    "BeachForecastItem",
    "BeachSunTime",
    "BeachTideItem",
    "BeachWaterTemperature",
    "BeachWaveHeight",
    "DataGoKrClient",
    "DataGoKrDatasetSpec",
    "DataGoKrItem",
    "ExpresswayRestAreaWeatherClient",
    "ForecastItem",
    "ForecastPrecipitationType",
    "GridPoint",
    "KmaAuthError",
    "KmaClient",
    "KmaEndpoint",
    "KmaError",
    "KmaParseError",
    "KmaRequestError",
    "KmaServerError",
    "KMA_DATA_GOKR_DATASETS",
    "LatLon",
    "MidForecastItem",
    "ObservedPrecipitationType",
    "RestAreaWeather",
    "ResponseMetadata",
    "SkyCode",
    "WeatherCategory",
    "WeatherSnapshot",
    "has_next_page",
    "iter_pages",
    "kma_grid_to_wgs84",
    "label_for",
    "make_cache_key",
    "next_page_no",
    "normalize_location",
    "parse_amount",
    "sanitize_request_params",
    "to_grid",
    "to_latlon",
    "unit_for",
    "wgs84_to_kma_grid",
]

"""Public enums for stable KMA identifiers."""

from __future__ import annotations

from enum import Enum


class KmaEndpoint(str, Enum):
    """Typed names for the supported VilageFcstInfoService_2.0 endpoints."""

    ULTRA_SRT_NCST = "getUltraSrtNcst"
    ULTRA_SRT_FCST = "getUltraSrtFcst"
    VILAGE_FCST = "getVilageFcst"
    FCST_VERSION = "getFcstVersion"


class WeatherCategory(str, Enum):
    """Common KMA forecast/observation category codes."""

    CURRENT_TEMPERATURE = "T1H"
    TEMPERATURE = "TMP"
    MIN_TEMPERATURE = "TMN"
    MAX_TEMPERATURE = "TMX"
    ONE_HOUR_RAIN = "RN1"
    PRECIPITATION = "PCP"
    SNOW = "SNO"
    HUMIDITY = "REH"
    EAST_WEST_WIND = "UUU"
    SOUTH_NORTH_WIND = "VVV"
    WIND_DIRECTION = "VEC"
    WIND_SPEED = "WSD"
    PRECIPITATION_PROBABILITY = "POP"
    WAVE_HEIGHT = "WAV"
    SKY = "SKY"
    PRECIPITATION_TYPE = "PTY"


class SkyCode(str, Enum):
    """KMA SKY code values."""

    CLEAR = "1"
    MOSTLY_CLOUDY = "3"
    CLOUDY = "4"


class ObservedPrecipitationType(str, Enum):
    """PTY values used by getUltraSrtNcst."""

    NONE = "0"
    RAIN = "1"
    RAIN_SNOW = "2"
    SNOW = "3"
    RAINDROPS = "5"
    RAINDROPS_SNOW_FLURRIES = "6"
    SNOW_FLURRIES = "7"


class ForecastPrecipitationType(str, Enum):
    """PTY values used by getUltraSrtFcst and getVilageFcst."""

    NONE = "0"
    RAIN = "1"
    RAIN_SNOW = "2"
    SNOW = "3"
    SHOWER = "4"


def enum_value(value: object) -> str:
    """Return a wire-format string for plain values and pykma enum values."""

    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def coerce_category(value: object) -> WeatherCategory | str:
    """Return `WeatherCategory` for known codes and the original code otherwise."""

    code = enum_value(value)
    try:
        return WeatherCategory(code)
    except ValueError:
        return code


def coerce_endpoint(value: object) -> KmaEndpoint | str:
    """Return `KmaEndpoint` for known endpoint names and the original name otherwise."""

    code = enum_value(value)
    try:
        return KmaEndpoint(code)
    except ValueError:
        return code


def category_or_none(value: object) -> WeatherCategory | None:
    """Return a category enum when `value` is a known KMA category code."""

    code = coerce_category(value)
    if isinstance(code, WeatherCategory):
        return code
    return None


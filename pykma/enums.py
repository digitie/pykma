"""안정적인 기상청 식별자를 위한 공개 enum."""

from __future__ import annotations

from enum import Enum


class KmaEndpoint(str, Enum):
    """지원하는 `VilageFcstInfoService_2.0` endpoint의 타입화된 이름."""

    ULTRA_SRT_NCST = "getUltraSrtNcst"
    ULTRA_SRT_FCST = "getUltraSrtFcst"
    VILAGE_FCST = "getVilageFcst"
    FCST_VERSION = "getFcstVersion"


class WeatherCategory(str, Enum):
    """자주 쓰는 기상청 예보/관측 category code."""

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
    """기상청 `SKY` code 값."""

    CLEAR = "1"
    MOSTLY_CLOUDY = "3"
    CLOUDY = "4"


class ObservedPrecipitationType(str, Enum):
    """`getUltraSrtNcst`에서 사용하는 `PTY` 값."""

    NONE = "0"
    RAIN = "1"
    RAIN_SNOW = "2"
    SNOW = "3"
    RAINDROPS = "5"
    RAINDROPS_SNOW_FLURRIES = "6"
    SNOW_FLURRIES = "7"


class ForecastPrecipitationType(str, Enum):
    """`getUltraSrtFcst`와 `getVilageFcst`에서 사용하는 `PTY` 값."""

    NONE = "0"
    RAIN = "1"
    RAIN_SNOW = "2"
    SNOW = "3"
    SHOWER = "4"


def enum_value(value: object) -> str:
    """일반 값과 `pykma` enum 값을 전송용 문자열로 반환합니다."""

    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def coerce_category(value: object) -> WeatherCategory | str:
    """알려진 code는 `WeatherCategory`로, 모르는 code는 원문 문자열로 반환합니다."""

    code = enum_value(value)
    try:
        return WeatherCategory(code)
    except ValueError:
        return code


def coerce_endpoint(value: object) -> KmaEndpoint | str:
    """알려진 endpoint 이름은 `KmaEndpoint`로, 모르는 이름은 원문 문자열로 반환합니다."""

    code = enum_value(value)
    try:
        return KmaEndpoint(code)
    except ValueError:
        return code


def category_or_none(value: object) -> WeatherCategory | None:
    """`value`가 알려진 기상청 category code일 때 category enum을 반환합니다."""

    code = coerce_category(value)
    if isinstance(code, WeatherCategory):
        return code
    return None

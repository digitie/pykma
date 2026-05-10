import json
from datetime import datetime

from pykma import (
    ForecastItem,
    ForecastPrecipitationType,
    GridPoint,
    KmaEndpoint,
    LatLon,
    ObservedPrecipitationType,
    SkyCode,
    WeatherCategory,
    label_for,
    unit_for,
)
from pykma.codes import normalize_value
from pykma.enums import category_or_none, coerce_category, coerce_endpoint
from pykma.time_utils import KST


def test_public_enums_keep_kma_wire_values() -> None:
    assert KmaEndpoint.ULTRA_SRT_NCST.value == "getUltraSrtNcst"
    assert WeatherCategory.TEMPERATURE == "TMP"
    assert SkyCode.CLEAR.value == "1"
    assert ObservedPrecipitationType.RAINDROPS.value == "5"
    assert ForecastPrecipitationType.SHOWER.value == "4"


def test_code_helpers_accept_enums() -> None:
    assert label_for(WeatherCategory.SKY, SkyCode.CLEAR) == "맑음"
    assert label_for(
        WeatherCategory.PRECIPITATION_TYPE,
        ObservedPrecipitationType.RAINDROPS,
        endpoint=KmaEndpoint.ULTRA_SRT_NCST,
    ) == "빗방울"
    assert normalize_value(WeatherCategory.TEMPERATURE, "12.3") == 12.3
    assert normalize_value(WeatherCategory.PRECIPITATION, "1.0mm 미만") == "1.0mm 미만"
    assert unit_for(WeatherCategory.TEMPERATURE) == "C"
    assert unit_for("UNKNOWN") is None


def test_coerce_helpers_preserve_unknown_values() -> None:
    assert coerce_category("TMP") is WeatherCategory.TEMPERATURE
    assert coerce_category("FOO") == "FOO"
    assert category_or_none("TMP") is WeatherCategory.TEMPERATURE
    assert category_or_none("FOO") is None
    assert coerce_endpoint("getVilageFcst") is KmaEndpoint.VILAGE_FCST
    assert coerce_endpoint("newEndpoint") == "newEndpoint"


def test_forecast_item_exposes_standardized_type_and_location_helpers() -> None:
    item = ForecastItem(
        base_at=datetime(2026, 5, 6, 14, 0, tzinfo=KST),
        forecast_at=datetime(2026, 5, 6, 15, 0, tzinfo=KST),
        nx=60,
        ny=127,
        category=WeatherCategory.TEMPERATURE,
        value=18.4,
        label=None,
    )

    assert item.category == "TMP"
    assert item.category_enum is WeatherCategory.TEMPERATURE
    assert item.unit == "C"
    assert item.grid == GridPoint(60, 127)
    assert isinstance(item.latlon, LatLon)
    assert item.coordinate is None
    assert item.model_dump(mode="json")["category"] == "TMP"
    assert json.loads(item.model_dump_json())["category"] == "TMP"
    assert json.dumps(item.model_dump(mode="json"), default=str)

from __future__ import annotations

from datetime import datetime
from typing import Callable

from pydantic import ValidationError

from kma import (
    ForecastItem,
    MidForecastItem,
    ResponseMetadata,
    WeatherCategory,
    WeatherSnapshot,
)
from kma.time_utils import KST


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> BaseException:
    try:
        func()
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def test_public_models_are_frozen_pydantic_models() -> None:
    metadata = ResponseMetadata(
        provider="data.go.kr",
        service_name="VilageFcstInfoService_2.0",
        endpoint="getVilageFcst",
        request_params={"serviceKey": "secret", "nx": 60},
    )
    item = ForecastItem(
        base_at=datetime(2026, 5, 6, 14, 0, tzinfo=KST),
        forecast_at=datetime(2026, 5, 6, 15, 0, tzinfo=KST),
        nx=60,
        ny=127,
        category="TMP",
        value=18.4,
        label=None,
        raw={"fcstValue": "18.4"},
        metadata=metadata,
    )

    assert item.category is WeatherCategory.TEMPERATURE
    assert item.model_dump(mode="json")["forecast_at"] == "2026-05-06T15:00:00+09:00"
    assert item.model_dump(mode="json")["metadata"]["request_params"] == {"nx": 60}
    assert "ForecastItem" in item.model_json_schema()["title"]
    assert_raises(ValidationError, lambda: setattr(item, "value", 20.0))


def test_mid_forecast_item_preserves_raw_without_grid_mapping() -> None:
    item = MidForecastItem(
        operation="getMidLandFcst",
        tm_fc="202605010600",
        reg_id="11B00000",
        raw={"regId": "11B00000", "wf3Am": "맑음"},
    )

    assert item.reg_id == "11B00000"
    assert item.raw["wf3Am"] == "맑음"


def test_public_models_validate_grid_bounds() -> None:
    assert_raises(
        ValidationError,
        lambda: WeatherSnapshot(
            observed_at=datetime(2026, 5, 6, 14, 0, tzinfo=KST),
            nx=0,
            ny=127,
            temperature=None,
            humidity=None,
            wind_speed=None,
            wind_direction=None,
            precipitation=None,
            sky_label=None,
            precipitation_label=None,
            raw={},
        ),
    )

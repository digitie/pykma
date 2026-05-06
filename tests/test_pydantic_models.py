from __future__ import annotations

from datetime import datetime
from typing import Callable

from pydantic import ValidationError

from pykma import ForecastItem, RestAreaWeather, WeatherCategory, WeatherSnapshot
from pykma.time_utils import KST


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> BaseException:
    try:
        func()
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def test_public_models_are_frozen_pydantic_models() -> None:
    item = ForecastItem(
        base_at=datetime(2026, 5, 6, 14, 0, tzinfo=KST),
        forecast_at=datetime(2026, 5, 6, 15, 0, tzinfo=KST),
        nx=60,
        ny=127,
        category="TMP",
        value=18.4,
        label=None,
    )

    assert item.category is WeatherCategory.TEMPERATURE
    assert item.model_dump(mode="json")["forecast_at"] == "2026-05-06T15:00:00+09:00"
    assert "ForecastItem" in item.model_json_schema()["title"]
    assert_raises(ValidationError, lambda: setattr(item, "value", 20.0))


def test_public_models_validate_grid_bounds_and_coordinates() -> None:
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
    assert_raises(
        ValidationError,
        lambda: RestAreaWeather(
            observed_at=datetime(2026, 5, 6, 14, 0, tzinfo=KST),
            sdate="20260506",
            std_hour="14",
            unit_code="001",
            unit_name="테스트휴게소",
            route_no="0010",
            route_name="경부선",
            direction_code=None,
            longitude=200.0,
            latitude=37.0,
            address=None,
            measurement_station=None,
            weather=None,
            temperature=None,
            humidity=None,
            wind_speed=None,
            wind_direction_code=None,
            rainfall=None,
            rainfall_strength=None,
            new_snow=None,
            snow=None,
            cloud=None,
            dew_point=None,
            raw={},
        ),
    )


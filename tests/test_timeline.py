from __future__ import annotations

from datetime import datetime

from kma import ForecastItem, WeatherCategory, pivot_forecast_items
from kma.time_utils import KST


def _item(
    category: str,
    value: str | float,
    *,
    forecast_hour: int = 15,
    label: str | None = None,
) -> ForecastItem:
    return ForecastItem(
        base_at=datetime(2026, 5, 13, 14, 0, tzinfo=KST),
        forecast_at=datetime(2026, 5, 13, forecast_hour, 0, tzinfo=KST),
        nx=60,
        ny=127,
        category=category,
        value=value,
        label=label,
        raw={"category": category, "fcstValue": value},
    )


def test_pivot_forecast_items_groups_rows_by_time_and_grid() -> None:
    timeline = pivot_forecast_items(
        [
            _item("TMP", 18.4),
            _item("SKY", "1", label="맑음"),
            _item("POP", 30.0, forecast_hour=16),
        ]
    )

    assert len(timeline) == 2
    first = timeline[0]
    assert first.forecast_at.isoformat() == "2026-05-13T15:00:00+09:00"
    assert first.values == {"TMP": 18.4, "SKY": "1"}
    assert first.labels == {"SKY": "맑음"}
    assert first.units["TMP"] == "C"
    assert first.value(WeatherCategory.TEMPERATURE) == 18.4
    assert first.label(WeatherCategory.SKY) == "맑음"
    assert first.grid.nx == 60
    assert first.raw_items[0]["category"] == "TMP"

    assert timeline[1].values == {"POP": 30.0}
    assert timeline[1].unit("POP") == "%"


def test_pivot_forecast_items_can_skip_raw_items() -> None:
    timeline = pivot_forecast_items([_item("TMP", 18.4)], include_raw=False)

    assert timeline[0].raw_items == []

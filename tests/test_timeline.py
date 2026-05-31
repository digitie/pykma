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


def test_pivot_forecast_items_empty_input_returns_empty_list() -> None:
    assert pivot_forecast_items([]) == []


def test_pivot_forecast_items_later_duplicate_overwrites_value() -> None:
    timeline = pivot_forecast_items(
        [
            _item("TMP", 18.4),
            _item("TMP", 19.9),  # same time/grid/category -> later wins
        ]
    )

    assert len(timeline) == 1
    assert timeline[0].values == {"TMP": 19.9}
    # raw_items preserves original order of both rows
    assert [row["fcstValue"] for row in timeline[0].raw_items] == [18.4, 19.9]


def test_pivot_forecast_items_separates_distinct_grids() -> None:
    other_grid = ForecastItem(
        base_at=datetime(2026, 5, 13, 14, 0, tzinfo=KST),
        forecast_at=datetime(2026, 5, 13, 15, 0, tzinfo=KST),
        nx=61,
        ny=127,
        category="TMP",
        value=10.0,
        label=None,
        raw={"category": "TMP", "fcstValue": 10.0},
    )

    timeline = pivot_forecast_items([_item("TMP", 18.4), other_grid])

    assert len(timeline) == 2
    grids = {(point.nx, point.ny) for point in timeline}
    assert grids == {(60, 127), (61, 127)}


def test_pivot_forecast_items_unknown_category_has_no_unit() -> None:
    timeline = pivot_forecast_items([_item("ZZZ", "x")])

    assert timeline[0].values == {"ZZZ": "x"}
    assert "ZZZ" not in timeline[0].units

"""예보 row를 시간축 단위로 평탄화하는 도우미."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .enums import enum_value
from .models import ForecastItem, ForecastTimepoint


def pivot_forecast_items(
    items: Iterable[ForecastItem],
    *,
    include_raw: bool = True,
) -> list[ForecastTimepoint]:
    """`ForecastItem` 목록을 `forecast_at`/격자 좌표별 시간대 객체로 묶습니다.

    KMA 단기예보 응답은 category별 row로 흩어져 있으므로 화면이나 저장 경계에서
    쓰기 전 시간대별 피벗이 필요할 때가 많습니다. 같은 시간대와 격자에서 category가
    중복되면 뒤쪽 항목이 `values`/`labels`를 덮어쓰고, `raw_items`에는 원문 순서를
    보존합니다.
    """

    grouped: dict[tuple[Any, int, int], dict[str, Any]] = {}
    for item in items:
        key = (item.forecast_at, item.nx, item.ny)
        group = grouped.get(key)
        if group is None:
            group = {
                "base_at": item.base_at,
                "forecast_at": item.forecast_at,
                "nx": item.nx,
                "ny": item.ny,
                "coordinate": item.coordinate,
                "values": {},
                "labels": {},
                "units": {},
                "raw_items": [],
                "metadata": item.metadata,
            }
            grouped[key] = group

        category = enum_value(item.category)
        group["values"][category] = item.value

        if item.label is not None:
            group["labels"][category] = item.label
        unit = item.unit
        if unit is not None:
            group["units"][category] = unit
        if include_raw:
            group["raw_items"].append(item.raw)

    return [ForecastTimepoint(**group) for group in grouped.values()]

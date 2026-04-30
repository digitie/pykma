"""Dataclasses returned by the public client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union


@dataclass(frozen=True)
class WeatherSnapshot:
    observed_at: datetime
    nx: int
    ny: int
    temperature: Optional[float]
    humidity: Optional[int]
    wind_speed: Optional[float]
    wind_direction: Optional[int]
    precipitation: Optional[float]
    sky_label: Optional[str]
    precipitation_label: Optional[str]
    raw: dict[str, Any]


@dataclass(frozen=True)
class ForecastItem:
    base_at: datetime
    forecast_at: datetime
    nx: int
    ny: int
    category: str
    value: Union[str, float]
    label: Optional[str]


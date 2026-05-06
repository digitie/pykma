"""Dataclasses returned by the public client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union

from .codes import unit_for
from .enums import WeatherCategory, category_or_none
from .locations import GridPoint, LatLon


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

    @property
    def grid(self) -> GridPoint:
        """Return this snapshot's KMA DFS grid coordinate."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """Return the approximate WGS84 coordinate for this snapshot's grid cell."""

        return self.grid.to_latlon()


@dataclass(frozen=True)
class ForecastItem:
    base_at: datetime
    forecast_at: datetime
    nx: int
    ny: int
    category: WeatherCategory | str
    value: Union[str, float]
    label: Optional[str]

    @property
    def category_enum(self) -> Optional[WeatherCategory]:
        """Return `WeatherCategory` when this item uses a known KMA category."""

        return category_or_none(self.category)

    @property
    def unit(self) -> Optional[str]:
        """Return the conventional unit for this item's category, if known."""

        return unit_for(self.category)

    @property
    def grid(self) -> GridPoint:
        """Return this forecast item's KMA DFS grid coordinate."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """Return the approximate WGS84 coordinate for this item's grid cell."""

        return self.grid.to_latlon()

"""Pydantic models returned by the public clients."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .codes import unit_for
from .enums import WeatherCategory, category_or_none, coerce_category
from .locations import GridPoint, LatLon


class PykmaModel(BaseModel):
    """Base class for immutable public pykma response models."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class WeatherSnapshot(PykmaModel):
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

    @model_validator(mode="after")
    def _validate_grid(self) -> "WeatherSnapshot":
        GridPoint(self.nx, self.ny)
        return self

    @property
    def grid(self) -> GridPoint:
        """Return this snapshot's KMA DFS grid coordinate."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """Return the approximate WGS84 coordinate for this snapshot's grid cell."""

        return self.grid.to_latlon()


class ForecastItem(PykmaModel):
    base_at: datetime
    forecast_at: datetime
    nx: int
    ny: int
    category: WeatherCategory | str
    value: Union[str, float]
    label: Optional[str]

    @field_validator("category", mode="before")
    @classmethod
    def _coerce_category(cls, value: object) -> WeatherCategory | str:
        return coerce_category(value)

    @model_validator(mode="after")
    def _validate_grid(self) -> "ForecastItem":
        GridPoint(self.nx, self.ny)
        return self

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


class RestAreaWeather(PykmaModel):
    observed_at: datetime
    sdate: str
    std_hour: str
    unit_code: str
    unit_name: str
    route_no: str
    route_name: str
    direction_code: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    address: Optional[str]
    measurement_station: Optional[str]
    weather: Optional[str]
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    wind_direction_code: Optional[str]
    rainfall: Optional[float]
    rainfall_strength: Optional[float]
    new_snow: Optional[float]
    snow: Optional[float]
    cloud: Optional[float]
    dew_point: Optional[float]
    raw: dict[str, Any]

    @model_validator(mode="after")
    def _validate_latlon(self) -> "RestAreaWeather":
        if self.latitude is not None and self.longitude is not None:
            LatLon(self.latitude, self.longitude)
        return self

    @property
    def latlon(self) -> Optional[LatLon]:
        """Return WGS84 location when the API row includes valid coordinates."""

        if self.latitude is None or self.longitude is None:
            return None
        return LatLon(self.latitude, self.longitude)

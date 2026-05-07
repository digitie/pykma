"""Pydantic models returned by the public clients."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .codes import unit_for
from .enums import WeatherCategory, category_or_none, coerce_category
from .locations import GridPoint, LatLon
from .metadata import ResponseMetadata


class PykmaModel(BaseModel):
    """Base class for immutable public pykma response models."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class WeatherSnapshot(PykmaModel):
    observed_at: datetime
    nx: int
    ny: int
    temperature: float | None
    humidity: int | None
    wind_speed: float | None
    wind_direction: int | None
    precipitation: float | None
    sky_label: str | None
    precipitation_label: str | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None

    @model_validator(mode="after")
    def _validate_grid(self) -> WeatherSnapshot:
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
    value: str | float
    label: str | None
    raw: dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata | None = None

    @field_validator("category", mode="before")
    @classmethod
    def _coerce_category(cls, value: object) -> WeatherCategory | str:
        return coerce_category(value)

    @model_validator(mode="after")
    def _validate_grid(self) -> ForecastItem:
        GridPoint(self.nx, self.ny)
        return self

    @property
    def category_enum(self) -> WeatherCategory | None:
        """Return `WeatherCategory` when this item uses a known KMA category."""

        return category_or_none(self.category)

    @property
    def unit(self) -> str | None:
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
    direction_code: str | None
    longitude: float | None
    latitude: float | None
    address: str | None
    measurement_station: str | None
    weather: str | None
    temperature: float | None
    humidity: float | None
    wind_speed: float | None
    wind_direction_code: str | None
    rainfall: float | None
    rainfall_strength: float | None
    new_snow: float | None
    snow: float | None
    cloud: float | None
    dew_point: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None

    @model_validator(mode="after")
    def _validate_latlon(self) -> RestAreaWeather:
        if self.latitude is not None and self.longitude is not None:
            LatLon(self.latitude, self.longitude)
        return self

    @property
    def latlon(self) -> LatLon | None:
        """Return WGS84 location when the API row includes valid coordinates."""

        if self.latitude is None or self.longitude is None:
            return None
        return LatLon(self.latitude, self.longitude)


class MidForecastItem(PykmaModel):
    """Typed row wrapper for KMA `MidFcstInfoService` responses.

    `reg_id` is the mid-term forecast region identifier from KMA. It is not
    interchangeable with short-term forecast `nx`/`ny` DFS grid coordinates,
    and pykma does not guess mappings between those coordinate systems.
    """

    operation: str
    tm_fc: str | None
    reg_id: str | None = None
    stn_id: str | None = None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None

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


class DataGoKrItem(PykmaModel):
    """Generic typed wrapper for data.go.kr rows without endpoint-specific models."""

    service: str
    operation: str
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachForecastItem(PykmaModel):
    """Forecast row from `BeachInfoservice` beach forecast endpoints."""

    operation: str
    base_at: datetime
    forecast_at: datetime
    beach_num: str
    category: WeatherCategory | str
    value: str | float
    label: str | None
    nx: int | None = None
    ny: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata | None = None

    @field_validator("category", mode="before")
    @classmethod
    def _coerce_category(cls, value: object) -> WeatherCategory | str:
        return coerce_category(value)

    @model_validator(mode="after")
    def _validate_optional_grid(self) -> BeachForecastItem:
        if (self.nx is None) != (self.ny is None):
            raise ValueError("nx and ny must be provided together")
        if self.nx is not None and self.ny is not None:
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
    def grid(self) -> GridPoint | None:
        """Return this forecast item's KMA DFS grid coordinate, when present."""

        if self.nx is None or self.ny is None:
            return None
        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon | None:
        """Return the approximate WGS84 coordinate for this item's grid cell."""

        grid = self.grid
        if grid is None:
            return None
        return grid.to_latlon()


class BeachWaveHeight(PykmaModel):
    """Wave-height observation row from `getWhBuoyBeach`."""

    observed_at: datetime
    beach_num: str
    wave_height: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachWaterTemperature(PykmaModel):
    """Water-temperature observation row from `getTwBuoyBeach`."""

    observed_at: datetime
    beach_num: str
    water_temperature: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachTideItem(PykmaModel):
    """Tide row from `getTideInfoBeach`."""

    base_date: str
    beach_num: str
    station_name: str | None
    tide_time: str | None
    tide_type: str | None
    tide_level: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachSunTime(PykmaModel):
    """Sunrise/sunset row from `getSunInfoBeach`."""

    base_date: str
    beach_num: str
    sunrise: str | None
    sunset: str | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


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

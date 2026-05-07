"""Standardized location value objects for pykma."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .grid import to_grid as _to_grid
from .grid import to_latlon as _to_latlon
from .grid import validate_grid as _validate_grid
from .grid import validate_latlon as _validate_latlon


@dataclass(frozen=True)
class LatLon:
    """WGS84 latitude/longitude coordinate.

    Use `lat` and `lon` as canonical field names. `latitude` and `longitude`
    properties are provided for integration with external geospatial code.
    """

    lat: float
    lon: float

    def __post_init__(self) -> None:
        lat = float(self.lat)
        lon = float(self.lon)
        _validate_latlon(lat, lon)
        object.__setattr__(self, "lat", lat)
        object.__setattr__(self, "lon", lon)

    @property
    def latitude(self) -> float:
        return self.lat

    @property
    def longitude(self) -> float:
        return self.lon

    @property
    def crs(self) -> str:
        return "EPSG:4326"

    def to_grid(self) -> GridPoint:
        nx, ny = _to_grid(self.lat, self.lon)
        return GridPoint(nx, ny)

    def as_tuple(self) -> tuple[float, float]:
        return self.lat, self.lon

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> LatLon:
        if "lat" in values and "lon" in values:
            return cls(float(values["lat"]), float(values["lon"]))
        if "latitude" in values and "longitude" in values:
            return cls(float(values["latitude"]), float(values["longitude"]))
        raise ValueError("location mapping must contain lat/lon or latitude/longitude")


@dataclass(frozen=True)
class GridPoint:
    """KMA DFS grid coordinate.

    `nx` and `ny` are not longitude/latitude. They are the grid coordinates used
    by KMA forecast APIs.
    """

    nx: int
    ny: int

    def __post_init__(self) -> None:
        nx = int(self.nx)
        ny = int(self.ny)
        _validate_grid(nx, ny)
        object.__setattr__(self, "nx", nx)
        object.__setattr__(self, "ny", ny)

    @property
    def grid_system(self) -> str:
        return "KMA_DFS"

    def to_latlon(self) -> LatLon:
        lat, lon = _to_latlon(self.nx, self.ny)
        return LatLon(lat, lon)

    def as_tuple(self) -> tuple[int, int]:
        return self.nx, self.ny

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> GridPoint:
        if "nx" in values and "ny" in values:
            return cls(int(values["nx"]), int(values["ny"]))
        raise ValueError("location mapping must contain nx/ny")


LocationInput = LatLon | GridPoint | Mapping[str, Any]


def normalize_location(
    location: LocationInput | None = None,
    *,
    lat: float | None = None,
    lon: float | None = None,
    nx: int | None = None,
    ny: int | None = None,
) -> GridPoint:
    """Normalize any supported location input to a KMA DFS grid point."""

    explicit = [lat is not None, lon is not None, nx is not None, ny is not None]
    if location is not None and any(explicit):
        raise ValueError("Provide either location or lat/lon or nx/ny, not multiple forms")

    if location is not None:
        return _normalize_location_object(location)

    has_latlon = lat is not None or lon is not None
    has_grid = nx is not None or ny is not None
    if has_latlon and has_grid:
        raise ValueError("Provide either lat/lon or nx/ny, not both")
    if has_latlon:
        if lat is None or lon is None:
            raise ValueError("Both lat and lon are required")
        return LatLon(lat, lon).to_grid()
    if has_grid:
        if nx is None or ny is None:
            raise ValueError("Both nx and ny are required")
        return GridPoint(nx, ny)
    raise ValueError("Either location, lat/lon, or nx/ny is required")


def _normalize_location_object(location: LocationInput) -> GridPoint:
    if isinstance(location, GridPoint):
        return location
    if isinstance(location, LatLon):
        return location.to_grid()
    if isinstance(location, Mapping):
        has_latlon = ("lat" in location and "lon" in location) or (
            "latitude" in location and "longitude" in location
        )
        has_grid = "nx" in location or "ny" in location
        if has_latlon and has_grid:
            raise ValueError("location mapping must not mix lat/lon and nx/ny")
        if has_latlon:
            return LatLon.from_mapping(location).to_grid()
        if has_grid:
            return GridPoint.from_mapping(location)
    raise TypeError("location must be LatLon, GridPoint, or a mapping")

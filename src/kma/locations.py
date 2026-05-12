"""`kma`에서 사용하는 표준 위치 값 객체."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from kraddr.base import PlaceCoordinate

from .grid import to_grid as _to_grid
from .grid import to_latlon as _to_latlon
from .grid import validate_grid as _validate_grid
from .grid import validate_latlon as _validate_latlon


@dataclass(frozen=True)
class LatLon:
    """WGS84 위도/경도 좌표.

    표준 필드명은 `lat`, `lon`입니다. 외부 지리정보 코드와 연결하기 쉽도록
    `latitude`, `longitude` 속성도 제공합니다.
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
    """기상청 DFS 격자 좌표.

    `nx`, `ny`는 위도/경도가 아니라 기상청 예보 API가 사용하는 격자 좌표입니다.
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


LocationInput = LatLon | GridPoint | PlaceCoordinate | Mapping[str, Any]


def normalize_location(
    location: LocationInput | None = None,
    *,
    lat: float | None = None,
    lon: float | None = None,
    nx: int | None = None,
    ny: int | None = None,
) -> GridPoint:
    """지원하는 위치 입력을 기상청 DFS `GridPoint`로 표준화합니다."""

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
    if isinstance(location, PlaceCoordinate):
        grid = location.to_kma_grid()
        return GridPoint(grid.nx, grid.ny)
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
    raise TypeError("location must be LatLon, GridPoint, PlaceCoordinate, or a mapping")

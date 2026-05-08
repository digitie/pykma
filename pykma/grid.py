"""기상청 LCC DFS 격자 변환 도우미."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .locations import GridPoint, LatLon

RE = 6371.00877
GRID = 5.0
SLAT1 = 30.0
SLAT2 = 60.0
OLON = 126.0
OLAT = 38.0
XO = 43
YO = 136
NX = 149
NY = 253


def validate_latlon(lat: float, lon: float) -> None:
    """기상청 격자로 투영하기 전에 WGS84 위도/경도를 검증합니다."""

    if not -90.0 <= lat <= 90.0:
        raise ValueError("lat must be between -90 and 90")
    if not -180.0 <= lon <= 180.0:
        raise ValueError("lon must be between -180 and 180")


def validate_grid(nx: int, ny: int) -> None:
    """공식 기상청 DFS 격자 범위를 검증합니다."""

    if not 1 <= nx <= NX:
        raise ValueError(f"nx must be between 1 and {NX}")
    if not 1 <= ny <= NY:
        raise ValueError(f"ny must be between 1 and {NY}")


def _project() -> tuple[float, float, float, float, float, float]:
    degrad = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * degrad
    slat2 = SLAT2 * degrad
    olon = OLON * degrad
    olat = OLAT * degrad

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(
        math.pi * 0.25 + slat1 * 0.5
    )
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf**sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro**sn)
    return degrad, re, sn, sf, ro, olon


def to_grid(lat: float, lon: float) -> tuple[int, int]:
    """WGS84 위도/경도를 기상청 `nx`, `ny` 격자 좌표로 변환합니다."""

    validate_latlon(lat, lon)
    degrad, re, sn, sf, ro, olon = _project()
    ra = math.tan(math.pi * 0.25 + lat * degrad * 0.5)
    ra = re * sf / (ra**sn)
    theta = lon * degrad - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    nx = int(ra * math.sin(theta) + XO + 0.5)
    ny = int(ro - ra * math.cos(theta) + YO + 0.5)
    return nx, ny


def to_latlon(nx: int, ny: int) -> tuple[float, float]:
    """기상청 `nx`, `ny` 격자 좌표를 WGS84 위도/경도로 역변환합니다."""

    validate_grid(nx, ny)
    degrad, re, sn, sf, ro, olon = _project()
    xn = nx - XO
    yn = ro - (ny - YO)
    ra = math.sqrt(xn * xn + yn * yn)
    if sn < 0:
        ra = -ra
    alat = (re * sf / ra) ** (1.0 / sn)
    alat = 2.0 * math.atan(alat) - math.pi * 0.5

    if abs(xn) <= 0.0:
        theta = 0.0
    elif abs(yn) <= 0.0:
        theta = math.pi * 0.5
        if xn < 0:
            theta = -theta
    else:
        theta = math.atan2(xn, yn)

    alon = theta / sn + olon
    return alat / degrad, alon / degrad


def wgs84_to_kma_grid(latitude: float, longitude: float) -> GridPoint:
    """WGS84 위도/경도를 `GridPoint`로 변환합니다.

    `latitude`/`longitude` 이름으로 좌표를 저장하는 application boundary에서
    명시적으로 쓰기 위한 공개 alias입니다.
    """

    from .locations import GridPoint

    nx, ny = to_grid(latitude, longitude)
    return GridPoint(nx, ny)


def kma_grid_to_wgs84(nx: int, ny: int) -> LatLon:
    """기상청 DFS `nx`/`ny` 좌표를 WGS84 `LatLon` 값으로 변환합니다."""

    from .locations import LatLon

    lat, lon = to_latlon(nx, ny)
    return LatLon(lat, lon)


latlon_to_grid = to_grid
grid_to_latlon = to_latlon

from typing import Callable

from pykrtour import PlaceCoordinate

from kma import GridPoint, LatLon, normalize_location


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> None:
    try:
        func()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def test_latlon_standardizes_wgs84_and_converts_to_grid() -> None:
    location = LatLon("37.5665", "126.9780")  # type: ignore[arg-type]

    assert location.lat == 37.5665
    assert location.lon == 126.978
    assert location.latitude == 37.5665
    assert location.longitude == 126.978
    assert location.crs == "EPSG:4326"
    assert location.as_tuple() == (37.5665, 126.978)
    assert location.to_grid() == GridPoint(60, 127)


def test_grid_point_standardizes_kma_dfs_and_converts_to_latlon() -> None:
    point = GridPoint("60", "127")  # type: ignore[arg-type]
    latlon = point.to_latlon()

    assert point.nx == 60
    assert point.ny == 127
    assert point.grid_system == "KMA_DFS"
    assert point.as_tuple() == (60, 127)
    assert abs(latlon.lat - 37.5665) < 0.05
    assert abs(latlon.lon - 126.9780) < 0.05


def test_normalize_location_accepts_objects_and_common_mappings() -> None:
    assert normalize_location(LatLon(37.5665, 126.9780)) == GridPoint(60, 127)
    assert normalize_location(GridPoint(60, 127)) == GridPoint(60, 127)
    assert normalize_location(PlaceCoordinate(lon=126.9780, lat=37.5665)) == GridPoint(60, 127)
    assert normalize_location({"lat": 37.5665, "lon": 126.9780}) == GridPoint(60, 127)
    assert normalize_location({"latitude": 37.5665, "longitude": 126.9780}) == GridPoint(60, 127)
    assert normalize_location({"nx": "60", "ny": "127"}) == GridPoint(60, 127)
    assert normalize_location(lat=37.5665, lon=126.9780) == GridPoint(60, 127)
    assert normalize_location(nx=60, ny=127) == GridPoint(60, 127)


def test_normalize_location_rejects_ambiguous_or_partial_inputs() -> None:
    assert_raises(ValueError, lambda: normalize_location(LatLon(37.5, 127.0), nx=60, ny=127))
    assert_raises(ValueError, lambda: normalize_location({"lat": 37.5, "lon": 127.0, "nx": 60}))
    assert_raises(ValueError, lambda: normalize_location({"nx": 60}))
    assert_raises(ValueError, lambda: normalize_location(lat=37.5))
    assert_raises(ValueError, lambda: normalize_location(nx=60))
    assert_raises(TypeError, lambda: normalize_location(object()))  # type: ignore[arg-type]

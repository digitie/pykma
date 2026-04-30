from typing import Callable

from pykma.grid import to_grid, to_latlon


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> None:
    try:
        func()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def test_to_grid_known_points() -> None:
    assert to_grid(37.5665, 126.9780) == (60, 127)
    assert to_grid(35.1796, 129.0756) == (98, 76)
    assert to_grid(33.4996, 126.5312) == (53, 38)
    assert to_grid(37.4979, 127.0276) == (61, 125)


def test_to_latlon_round_trip_is_close() -> None:
    lat, lon = to_latlon(60, 127)
    assert abs(lat - 37.5665) < 0.05
    assert abs(lon - 126.9780) < 0.05


def test_coordinate_bounds_are_validated() -> None:
    assert_raises(ValueError, lambda: to_grid(90.1, 126.0))
    assert_raises(ValueError, lambda: to_grid(37.0, 180.1))
    assert_raises(ValueError, lambda: to_latlon(0, 127))
    assert_raises(ValueError, lambda: to_latlon(60, 254))

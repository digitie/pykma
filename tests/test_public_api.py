import pykma


def test_package_all_contains_recommended_public_api() -> None:
    recommended = {
        "KmaClient",
        "DataGoKrClient",
        "ApiHubClient",
        "ExpresswayRestAreaWeatherClient",
        "LatLon",
        "GridPoint",
        "normalize_location",
        "to_grid",
        "to_latlon",
        "wgs84_to_kma_grid",
        "kma_grid_to_wgs84",
        "ResponseMetadata",
        "sanitize_request_params",
        "make_cache_key",
        "has_next_page",
        "next_page_no",
        "iter_pages",
    }

    assert recommended.issubset(set(pykma.__all__))

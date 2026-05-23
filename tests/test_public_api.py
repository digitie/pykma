import kma


def test_package_all_contains_recommended_public_api() -> None:
    recommended = {
        "KmaClient",
        "DataGoKrClient",
        "DataGoKrDatasetSpec",
        "KMA_DATA_GOKR_DATASETS",
        "ApiHubClient",
        "ApiCatalogEntry",
        "BeachForecastItem",
        "BeachWaveHeight",
        "BeachWaterTemperature",
        "BeachTideItem",
        "BeachSunTime",
        "DataGoKrItem",
        "ForecastTimepoint",
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
        "base_available_at",
        "cache_expire_at",
        "latest_mid_fcst_base",
        "latest_mid_fcst_time",
        "pivot_forecast_items",
        "has_next_page",
        "api_catalog",
        "api_key_for_gateway",
        "env_names_for_gateway",
        "load_local_env",
        "next_page_no",
        "iter_pages",
    }

    assert recommended.issubset(set(kma.__all__))

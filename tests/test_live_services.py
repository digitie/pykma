from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import pytest

from kma import (
    ApiHubClient,
    ApiHubGeneratedClient,
    ApiHubResponse,
    DataGoKrClient,
)
from kma.time_utils import latest_ultra_srt_ncst_base

pytestmark = pytest.mark.integration


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env.local"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()

RUN_LIVE = os.getenv("KMA_RUN_LIVE") == "1"


def _apihub_key() -> str | None:
    return os.getenv("KMA_APIHUB_AUTH_KEY") or os.getenv("KMA_APIHUB_KEY")


def _data_gokr_key() -> str | None:
    return os.getenv("DATA_GOKR_SERVICE_KEY") or os.getenv("KMA_SERVICE_KEY")


def _items_from_body(body: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_items = body["items"]  # type: ignore[index]
    item = raw_items["item"]  # type: ignore[index]
    if isinstance(item, list):
        return item
    if isinstance(item, Mapping):
        return [item]
    raise AssertionError("body.items.item is not a list or mapping")


def _assert_apihub_response_is_sanitized(response: ApiHubResponse) -> None:
    key = _apihub_key()
    assert key is not None
    assert "authKey=***" in response.url
    assert key not in response.url
    assert response.metadata is not None
    assert "authKey" not in response.metadata.request_params


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _apihub_key(), reason="KMA_APIHUB_AUTH_KEY is not set")
def test_live_apihub_forecast_region_endpoints_shape() -> None:
    client = ApiHubGeneratedClient(_apihub_key() or "", timeout=30, retries=1)

    responses = [
        client.fct_shrt_reg(use_sample=True),
        client.fct_medm_reg(use_sample=True),
    ]

    for response in responses:
        table = response.text_table()

        assert response.status_code == 200
        assert response.content
        assert response.text.strip()
        _assert_apihub_response_is_sanitized(response)
        assert table.raw_lines
        assert "SERVICE_KEY" not in response.text.upper()


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _apihub_key(), reason="KMA_APIHUB_AUTH_KEY is not set")
def test_live_apihub_warning_impact_and_zone_endpoints_shape() -> None:
    generated = ApiHubGeneratedClient(_apihub_key() or "", timeout=30, retries=1)
    generic = ApiHubClient(_apihub_key() or "", timeout=30, retries=1)

    text_responses = [
        generated.wrn_reg(use_sample=True),
        generated.ifs_fct_pstt(use_sample=True),
    ]

    for response in text_responses:
        table = response.text_table()

        assert response.status_code == 200
        assert response.content
        assert response.text.strip()
        _assert_apihub_response_is_sanitized(response)
        assert table.raw_lines
        assert "SERVICE_KEY" not in response.text.upper()

    zone_response = generic.open_api(
        "FcstZoneInfoService",
        "getFcstZoneCd",
        {"regId": "11A00101"},
        data_type="JSON",
        num_of_rows=10,
    )
    payload = zone_response.json()
    body = payload["response"]["body"]

    assert zone_response.status_code == 200
    _assert_apihub_response_is_sanitized(zone_response)
    assert payload["response"]["header"]["resultCode"] == "00"
    assert body["items"]["item"]
    assert int(body["totalCount"]) >= 1


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GOKR_SERVICE_KEY or KMA_SERVICE_KEY is not set",
)
def test_live_data_gokr_ultra_srt_ncst_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)
    base_date, base_time = latest_ultra_srt_ncst_base()

    body = client.request(
        "VilageFcstInfoService_2.0",
        "getUltraSrtNcst",
        {
            "base_date": base_date,
            "base_time": base_time,
            "nx": 60,
            "ny": 127,
        },
        num_of_rows=100,
    )
    items = _items_from_body(body)

    assert items
    assert any(item.get("category") == "T1H" for item in items)
    assert all(str(item.get("nx")) == "60" for item in items)
    assert all(str(item.get("ny")) == "127" for item in items)

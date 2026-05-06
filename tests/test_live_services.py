from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import pytest

from pykma import ApiHubGeneratedClient, DataGoKrClient, ExpresswayRestAreaWeatherClient
from pykma.exceptions import KmaAuthError
from pykma.time_utils import latest_ultra_srt_ncst_base

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

RUN_LIVE = os.getenv("PYKMA_RUN_LIVE") == "1"


def _apihub_key() -> str | None:
    return os.getenv("KMA_APIHUB_AUTH_KEY") or os.getenv("KMA_APIHUB_KEY")


def _data_gokr_key() -> str | None:
    return os.getenv("DATA_GOKR_SERVICE_KEY") or os.getenv("KMA_SERVICE_KEY")


def _expressway_key() -> str | None:
    return os.getenv("EXPRESSWAY_API_KEY") or os.getenv("KOREA_EXPRESSWAY_API_KEY")


def _items_from_body(body: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_items = body["items"]  # type: ignore[index]
    item = raw_items["item"]  # type: ignore[index]
    if isinstance(item, list):
        return item
    if isinstance(item, Mapping):
        return [item]
    raise AssertionError("body.items.item is not a list or mapping")


@pytest.mark.skipif(not RUN_LIVE, reason="set PYKMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _apihub_key(), reason="KMA_APIHUB_AUTH_KEY is not set")
def test_live_apihub_generated_text_endpoint_shape() -> None:
    client = ApiHubGeneratedClient(_apihub_key() or "", timeout=30, retries=1)

    try:
        response = client.kma_sfctm2(tm="202211300900", stn="108", help="1")
    except KmaAuthError as exc:
        message = str(exc)
        if "403" in message or "활용신청" in message:
            pytest.skip("APIHub key reached the server but is not approved for this endpoint")
        raise
    table = response.text_table()

    assert response.status_code == 200
    assert response.content
    assert response.text.strip()
    assert "authKey=***" in response.url
    assert _apihub_key() not in response.url
    assert table.raw_lines
    assert "SERVICE_KEY" not in response.text.upper()


@pytest.mark.skipif(not RUN_LIVE, reason="set PYKMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _data_gokr_key(), reason="DATA_GOKR_SERVICE_KEY or KMA_SERVICE_KEY is not set")
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


@pytest.mark.skipif(not RUN_LIVE, reason="set PYKMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _expressway_key(), reason="EXPRESSWAY_API_KEY is not set")
def test_live_expressway_rest_area_weather_shape() -> None:
    client = ExpresswayRestAreaWeatherClient(_expressway_key() or "", timeout=30, retries=1)

    rows = client.latest_weather(lookback_hours=72)

    assert rows
    assert rows[0].unit_name
    assert rows[0].route_name
    assert rows[0].observed_at.tzinfo is not None
    assert rows[0].raw

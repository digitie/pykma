from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kma import (
    ApiHubClient,
    ApiHubGeneratedClient,
    ApiHubResponse,
    AsosDailyItem,
    AsosHourlyItem,
    DataGoKrClient,
    ForecastItem,
    KmaClient,
    MidForecastItem,
    WeatherWarningItem,
)
from kma.exceptions import KmaAuthError
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
    return os.getenv("DATA_GO_KR_SERVICE_KEY") or os.getenv("DATA_GO_KR_SERVICE_KEY")


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
    reason="DATA_GO_KR_SERVICE_KEY is not set",
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


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_async_kma_forecast_facade_shape() -> None:
    async def run() -> None:
        async with KmaClient.aio(_data_gokr_key() or "", timeout=30, retries=1) as client:
            snapshot = await client.forecast.now(nx=60, ny=127)

        assert snapshot.metadata is not None
        assert snapshot.metadata.endpoint == "getUltraSrtNcst"
        assert snapshot.grid.nx == 60
        assert snapshot.grid.ny == 127
        assert snapshot.raw["items"]

    asyncio.run(run())


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_async_data_gokr_facade_shape() -> None:
    async def run() -> None:
        base_date, base_time = latest_ultra_srt_ncst_base()
        async with DataGoKrClient.aio(_data_gokr_key() or "", timeout=30, retries=1) as client:
            items = await client.items(
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

        assert items
        assert any(item.get("category") == "T1H" for item in items)

    asyncio.run(run())


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_data_gokr_asos_daily_typed_model_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)

    try:
        rows = client.asos_daily_weather(
            start_dt="20240101",
            end_dt="20240102",
            stn_ids=108,
            num_of_rows=10,
        )
    except KmaAuthError as exc:  # 서비스키 미구독 — docs/live-test-key-issues.md 참고
        pytest.skip(f"AsosDalyInfoService not authorized for this service key: {exc}")

    assert rows
    assert all(isinstance(row, AsosDailyItem) for row in rows)
    assert rows[0].stn_id == "108"
    assert rows[0].date
    assert rows[0].metadata is not None
    assert "serviceKey" not in rows[0].metadata.request_params


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_data_gokr_asos_hourly_typed_model_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)

    try:
        rows = client.asos_hourly_weather(
            start_dt="20240101",
            start_hh=0,
            end_dt="20240101",
            end_hh=3,
            stn_ids=108,
            num_of_rows=10,
        )
    except KmaAuthError as exc:  # 서비스키 미구독 — docs/live-test-key-issues.md 참고
        pytest.skip(f"AsosHourlyInfoService not authorized for this service key: {exc}")

    assert rows
    assert all(isinstance(row, AsosHourlyItem) for row in rows)
    assert rows[0].stn_id == "108"
    assert rows[0].observed_at
    assert rows[0].metadata is not None


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_data_gokr_weather_warning_typed_model_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)

    # getWthrWrnList 는 현재 시각 기준 최근 6일 이내만 조회 가능하므로 실시간으로 범위를 잡는다.
    now = datetime.now()
    from_tm_fc = (now - timedelta(days=3)).strftime("%Y%m%d")
    to_tm_fc = now.strftime("%Y%m%d")

    try:
        # NO_DATA(resultCode 03)는 예외 대신 빈 list로 정규화된다 (#18).
        rows = client.weather_warning_list(
            stn_id=108,
            from_tm_fc=from_tm_fc,
            to_tm_fc=to_tm_fc,
            num_of_rows=10,
        )
    except KmaAuthError as exc:  # 서비스키 미구독 — docs/live-test-key-issues.md 참고
        pytest.skip(f"WthrWrnInfoService not authorized for this service key: {exc}")

    assert all(isinstance(row, WeatherWarningItem) for row in rows)
    for row in rows:
        assert row.metadata is not None
        assert "serviceKey" not in row.metadata.request_params


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(not _apihub_key(), reason="KMA_APIHUB_AUTH_KEY is not set")
def test_live_async_apihub_facade_shape() -> None:
    async def run() -> None:
        async with ApiHubClient.aio(_apihub_key() or "", timeout=30, retries=1) as client:
            response = await client.open_api(
                "FcstZoneInfoService",
                "getFcstZoneCd",
                {"regId": "11A00101"},
                data_type="JSON",
                num_of_rows=10,
            )

        payload = response.json()
        assert response.status_code == 200
        _assert_apihub_response_is_sanitized(response)
        assert payload["response"]["header"]["resultCode"] == "00"

    asyncio.run(run())


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_data_gokr_mid_land_forecast_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)

    try:
        rows = client.mid_land_forecast(reg_id="11B00000", num_of_rows=10)
    except KmaAuthError as exc:  # 서비스키 미구독 — docs/live-test-key-issues.md 참고
        pytest.skip(f"MidFcstInfoService not authorized for this service key: {exc}")

    if not rows:  # NO_DATA(03)는 빈 결과로 정규화된다 — 발표시각 데이터 아직 없음 (정상)
        pytest.skip("MidFcstInfoService returned NO_DATA for the chosen tmFc")

    assert rows
    assert all(isinstance(row, MidForecastItem) for row in rows)
    assert rows[0].operation == "getMidLandFcst"
    assert rows[0].metadata is not None
    assert "serviceKey" not in rows[0].metadata.request_params


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_data_gokr_land_forecast_message_shape() -> None:
    client = DataGoKrClient(_data_gokr_key() or "", timeout=30, retries=1)

    try:
        rows = client.land_forecast_message(reg_id="11B10101", num_of_rows=10)
    except KmaAuthError as exc:  # 서비스키 미구독 — docs/live-test-key-issues.md 참고
        pytest.skip(f"VilageFcstMsgService not authorized for this service key: {exc}")

    if not rows:  # NO_DATA(03)는 빈 결과로 정규화된다
        pytest.skip("VilageFcstMsgService returned NO_DATA")

    assert rows
    assert rows[0].operation == "getLandFcst"
    assert rows[0].metadata is not None


@pytest.mark.skipif(not RUN_LIVE, reason="set KMA_RUN_LIVE=1 to call real servers")
@pytest.mark.skipif(
    not _data_gokr_key(),
    reason="DATA_GO_KR_SERVICE_KEY is not set",
)
def test_live_kma_vilage_forecast_short_shape() -> None:
    client = KmaClient(_data_gokr_key() or "", timeout=30, retries=1)

    items = client.forecast_short(nx=60, ny=127)

    assert items
    assert all(isinstance(item, ForecastItem) for item in items)
    assert all(item.nx == 60 and item.ny == 127 for item in items)
    assert items[0].metadata is not None
    assert items[0].forecast_at.tzinfo is not None  # KST aware

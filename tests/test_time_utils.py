from datetime import datetime, timezone

from kma.time_utils import (
    KST,
    as_kst,
    base_available_at,
    cache_expire_at,
    latest_mid_fcst_base,
    latest_mid_fcst_time,
    latest_ultra_srt_fcst_base,
    latest_ultra_srt_ncst_base,
    latest_vilage_base,
    parse_kma_datetime,
)


def test_latest_ultra_srt_ncst_base_waits_until_40_minutes() -> None:
    assert latest_ultra_srt_ncst_base(datetime(2026, 4, 30, 14, 35, tzinfo=KST)) == (
        "20260430",
        "1300",
    )
    assert latest_ultra_srt_ncst_base(datetime(2026, 4, 30, 14, 45, tzinfo=KST)) == (
        "20260430",
        "1400",
    )


def test_latest_ultra_srt_fcst_base_waits_until_45_minutes() -> None:
    assert latest_ultra_srt_fcst_base(datetime(2026, 4, 30, 14, 44, tzinfo=KST)) == (
        "20260430",
        "1330",
    )
    assert latest_ultra_srt_fcst_base(datetime(2026, 4, 30, 14, 50, tzinfo=KST)) == (
        "20260430",
        "1430",
    )


def test_latest_vilage_base_uses_previous_day_before_first_release() -> None:
    assert latest_vilage_base(datetime(2026, 4, 30, 2, 5, tzinfo=KST)) == (
        "20260429",
        "2300",
    )
    assert latest_vilage_base(datetime(2026, 4, 30, 2, 15, tzinfo=KST)) == (
        "20260430",
        "0200",
    )


def test_latest_mid_fcst_base_waits_until_release_delay() -> None:
    assert latest_mid_fcst_base(datetime(2026, 5, 1, 6, 5, tzinfo=KST)) == (
        "20260430",
        "1800",
    )
    assert latest_mid_fcst_base(datetime(2026, 5, 1, 6, 15, tzinfo=KST)) == (
        "20260501",
        "0600",
    )
    assert latest_mid_fcst_time(datetime(2026, 5, 1, 18, 15, tzinfo=KST)) == "202605011800"


def test_base_available_at_and_cache_expire_at_follow_endpoint_schedule() -> None:
    assert base_available_at("getVilageFcst", "20260430", "1100").isoformat() == (
        "2026-04-30T11:10:00+09:00"
    )
    assert cache_expire_at("getVilageFcst", "20260430", "1100").isoformat() == (
        "2026-04-30T14:10:00+09:00"
    )
    assert cache_expire_at("getVilageFcst", "20260430", "2300").isoformat() == (
        "2026-05-01T02:10:00+09:00"
    )
    assert cache_expire_at("getUltraSrtFcst", "20260430", "1430").isoformat() == (
        "2026-04-30T15:45:00+09:00"
    )
    assert cache_expire_at("getMidLandFcst", "20260501", "0600").isoformat() == (
        "2026-05-01T18:10:00+09:00"
    )


def test_naive_datetime_is_interpreted_as_kst() -> None:
    assert as_kst(datetime(2026, 4, 30, 14, 0)).tzinfo == KST
    assert latest_ultra_srt_ncst_base(datetime(2026, 4, 30, 14, 45)) == (
        "20260430",
        "1400",
    )


def test_aware_datetime_is_converted_to_kst() -> None:
    assert latest_ultra_srt_ncst_base(datetime(2026, 4, 30, 5, 45, tzinfo=timezone.utc)) == (
        "20260430",
        "1400",
    )


def test_parse_kma_datetime_returns_kst_aware_datetime() -> None:
    parsed = parse_kma_datetime("20260430", "1430")
    assert parsed.isoformat() == "2026-04-30T14:30:00+09:00"

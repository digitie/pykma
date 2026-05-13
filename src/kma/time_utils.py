"""기상청 endpoint용 KST 기준 base date/time 계산."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from .enums import KmaEndpoint, enum_value

KST = timezone(timedelta(hours=9))
VILAGE_PUBLISH_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)
MID_FCST_PUBLISH_HOURS = (6, 18)
ULTRA_SRT_NCST_DELAY = timedelta(minutes=40)
ULTRA_SRT_FCST_DELAY = timedelta(minutes=15)
VILAGE_FCST_DELAY = timedelta(minutes=10)
MID_FCST_DELAY = timedelta(minutes=10)

_MID_FCST_OPERATIONS = {
    "MidFcstInfoService",
    "getMidFcst",
    "getMidLandFcst",
    "getMidTa",
    "getMidSeaFcst",
}


def as_kst(when: datetime | None = None) -> datetime:
    """한국표준시 timezone-aware `datetime`을 반환합니다."""

    if when is None:
        return datetime.now(KST)
    if when.tzinfo is None:
        return when.replace(tzinfo=KST)
    return when.astimezone(KST)


def format_base(base_at: datetime) -> tuple[str, str]:
    base_at = as_kst(base_at)
    return base_at.strftime("%Y%m%d"), base_at.strftime("%H%M")


def latest_ultra_srt_ncst_base(when: datetime | None = None) -> tuple[str, str]:
    """`getUltraSrtNcst`에서 사용할 수 있는 최신 base를 반환합니다.

    관측값은 매시 `HH:00`에 발표되고 보통 `HH:40` 이후 조회 가능합니다.
    """

    cutoff = as_kst(when) - ULTRA_SRT_NCST_DELAY
    base_at = cutoff.replace(minute=0, second=0, microsecond=0)
    return format_base(base_at)


def latest_ultra_srt_fcst_base(when: datetime | None = None) -> tuple[str, str]:
    """`getUltraSrtFcst`에서 사용할 수 있는 최신 base를 반환합니다.

    예보는 매시 `HH:30`에 발표되고 보통 `HH:45` 이후 조회 가능합니다.
    """

    cutoff = as_kst(when) - ULTRA_SRT_FCST_DELAY
    if cutoff.minute >= 30:
        base_at = cutoff.replace(minute=30, second=0, microsecond=0)
    else:
        base_at = (cutoff - timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)
    return format_base(base_at)


def latest_vilage_base(when: datetime | None = None) -> tuple[str, str]:
    """`getVilageFcst`에서 사용할 수 있는 최신 base를 반환합니다."""

    return _latest_base_for_hours(when, VILAGE_PUBLISH_HOURS, delay=VILAGE_FCST_DELAY)


def latest_mid_fcst_base(when: datetime | None = None) -> tuple[str, str]:
    """중기예보 `tmFc`에 사용할 수 있는 최신 발표 기준시각을 반환합니다."""

    return _latest_base_for_hours(when, MID_FCST_PUBLISH_HOURS, delay=MID_FCST_DELAY)


def latest_mid_fcst_time(when: datetime | None = None) -> str:
    """중기예보 `tmFc` 파라미터용 `YYYYMMDDHHMM` 문자열을 반환합니다."""

    base_date, base_time = latest_mid_fcst_base(when)
    return f"{base_date}{base_time}"


def base_available_at(
    endpoint: str | KmaEndpoint,
    base_date: str,
    base_time: str,
) -> datetime:
    """해당 endpoint의 base data가 조회 가능해지는 KST 시각을 반환합니다."""

    return parse_kma_datetime(base_date, base_time) + _availability_delay(endpoint)


def cache_expire_at(
    endpoint: str | KmaEndpoint,
    base_date: str,
    base_time: str,
) -> datetime:
    """base data cache를 자연 만료시키기 좋은 다음 발표 조회 가능 시각을 반환합니다."""

    base_at = parse_kma_datetime(base_date, base_time)
    next_base = _next_publish_at(endpoint, base_at)
    return next_base + _availability_delay(endpoint)


def parse_kma_datetime(date_value: str, time_value: str) -> datetime:
    """기상청 `YYYYMMDD`와 `HHMM` 필드를 KST aware `datetime`으로 파싱합니다."""

    return datetime.strptime(f"{date_value}{time_value}", "%Y%m%d%H%M").replace(tzinfo=KST)


def _latest_base_for_hours(
    when: datetime | None,
    publish_hours: Sequence[int],
    *,
    delay: timedelta,
) -> tuple[str, str]:
    cutoff = as_kst(when) - delay
    candidates = [
        cutoff.replace(hour=hour, minute=0, second=0, microsecond=0)
        for hour in publish_hours
    ]
    usable = [candidate for candidate in candidates if candidate <= cutoff]
    if usable:
        return format_base(max(usable))

    previous = (cutoff - timedelta(days=1)).replace(
        hour=max(publish_hours),
        minute=0,
        second=0,
        microsecond=0,
    )
    return format_base(previous)


def _availability_delay(endpoint: str | KmaEndpoint) -> timedelta:
    endpoint_code = enum_value(endpoint)
    if endpoint_code == KmaEndpoint.ULTRA_SRT_NCST.value:
        return ULTRA_SRT_NCST_DELAY
    if endpoint_code == KmaEndpoint.ULTRA_SRT_FCST.value:
        return ULTRA_SRT_FCST_DELAY
    if endpoint_code == KmaEndpoint.VILAGE_FCST.value:
        return VILAGE_FCST_DELAY
    if endpoint_code in _MID_FCST_OPERATIONS:
        return MID_FCST_DELAY
    raise ValueError(f"unsupported endpoint schedule: {endpoint_code}")


def _next_publish_at(endpoint: str | KmaEndpoint, base_at: datetime) -> datetime:
    endpoint_code = enum_value(endpoint)
    base_at = as_kst(base_at).replace(second=0, microsecond=0)
    if endpoint_code == KmaEndpoint.ULTRA_SRT_NCST.value:
        return _next_hourly_publish_at(base_at, minute=0)
    if endpoint_code == KmaEndpoint.ULTRA_SRT_FCST.value:
        return _next_hourly_publish_at(base_at, minute=30)
    if endpoint_code == KmaEndpoint.VILAGE_FCST.value:
        return _next_publish_from_hours(base_at, VILAGE_PUBLISH_HOURS)
    if endpoint_code in _MID_FCST_OPERATIONS:
        return _next_publish_from_hours(base_at, MID_FCST_PUBLISH_HOURS)
    raise ValueError(f"unsupported endpoint schedule: {endpoint_code}")


def _next_hourly_publish_at(base_at: datetime, *, minute: int) -> datetime:
    candidate = base_at.replace(minute=minute)
    if candidate <= base_at:
        return candidate + timedelta(hours=1)
    return candidate


def _next_publish_from_hours(base_at: datetime, publish_hours: Sequence[int]) -> datetime:
    for hour in publish_hours:
        candidate = base_at.replace(hour=hour, minute=0)
        if candidate > base_at:
            return candidate
    return (base_at + timedelta(days=1)).replace(hour=publish_hours[0], minute=0)

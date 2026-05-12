"""기상청 endpoint용 KST 기준 base date/time 계산."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
VILAGE_PUBLISH_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)


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

    cutoff = as_kst(when) - timedelta(minutes=40)
    base_at = cutoff.replace(minute=0, second=0, microsecond=0)
    return format_base(base_at)


def latest_ultra_srt_fcst_base(when: datetime | None = None) -> tuple[str, str]:
    """`getUltraSrtFcst`에서 사용할 수 있는 최신 base를 반환합니다.

    예보는 매시 `HH:30`에 발표되고 보통 `HH:45` 이후 조회 가능합니다.
    """

    cutoff = as_kst(when) - timedelta(minutes=15)
    if cutoff.minute >= 30:
        base_at = cutoff.replace(minute=30, second=0, microsecond=0)
    else:
        base_at = (cutoff - timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)
    return format_base(base_at)


def latest_vilage_base(when: datetime | None = None) -> tuple[str, str]:
    """`getVilageFcst`에서 사용할 수 있는 최신 base를 반환합니다."""

    cutoff = as_kst(when) - timedelta(minutes=10)
    candidates = [
        cutoff.replace(hour=hour, minute=0, second=0, microsecond=0)
        for hour in VILAGE_PUBLISH_HOURS
    ]
    usable = [candidate for candidate in candidates if candidate <= cutoff]
    if usable:
        return format_base(max(usable))

    previous = (cutoff - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
    return format_base(previous)


def parse_kma_datetime(date_value: str, time_value: str) -> datetime:
    """기상청 `YYYYMMDD`와 `HHMM` 필드를 KST aware `datetime`으로 파싱합니다."""

    return datetime.strptime(f"{date_value}{time_value}", "%Y%m%d%H%M").replace(tzinfo=KST)

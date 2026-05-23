"""API 응답 값 변환용 공유 파싱 도우미."""

from __future__ import annotations


def float_or_none(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def int_or_none(value: object) -> int | None:
    number = float_or_none(value)
    if number is None:
        return None
    return int(number)


def str_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

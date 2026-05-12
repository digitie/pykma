"""data.go.kr 스타일 응답 body용 페이지네이션 도우미."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import Any


def has_next_page(body: Mapping[str, Any]) -> bool:
    """data.go.kr 응답 body에 다음 페이지가 있는지 반환합니다."""

    page_no = _int_from_body(body, "pageNo", default=1)
    num_of_rows = _int_from_body(body, "numOfRows", default=0)
    total_count = _int_from_body(body, "totalCount", default=0)
    if page_no < 1 or num_of_rows < 1 or total_count < 1:
        return False
    return page_no * num_of_rows < total_count


def next_page_no(body: Mapping[str, Any]) -> int | None:
    """다음 페이지 번호를 반환하고, 마지막 페이지이면 `None`을 반환합니다."""

    if not has_next_page(body):
        return None
    return _int_from_body(body, "pageNo", default=1) + 1


def iter_pages(
    fetch_page: Callable[[int], Mapping[str, Any]],
    *,
    start_page: int = 1,
    max_pages: int = 100,
    max_items: int | None = None,
) -> Iterator[Mapping[str, Any]]:
    """`pageNo` metadata를 따라 data.go.kr 응답 body를 순회합니다.

    `max_pages`와 `max_items`는 upstream API가 일관되지 않은 페이지네이션
    metadata를 반환할 때 무한 루프를 막는 명시적 안전장치입니다.
    """

    if start_page < 1:
        raise ValueError("start_page must be >= 1")
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")
    if max_items is not None and max_items < 1:
        raise ValueError("max_items must be >= 1")

    page_no = start_page
    pages_seen = 0
    items_seen = 0
    while pages_seen < max_pages:
        body = fetch_page(page_no)
        yield body

        pages_seen += 1
        items_seen += _item_count(body)
        if max_items is not None and items_seen >= max_items:
            return

        next_page = next_page_no(body)
        if next_page is None:
            return
        page_no = next_page


def _int_from_body(body: Mapping[str, Any], key: str, *, default: int) -> int:
    try:
        return int(str(body.get(key, default)).strip())
    except (TypeError, ValueError):
        return default


def _item_count(body: Mapping[str, Any]) -> int:
    items = body.get("items")
    if not isinstance(items, Mapping):
        return 0
    raw = items.get("item")
    if isinstance(raw, list):
        return len(raw)
    if isinstance(raw, Mapping):
        return 1
    return 0

"""Pagination helpers for data.go.kr-style response bodies."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import Any


def has_next_page(body: Mapping[str, Any]) -> bool:
    """Return whether a data.go.kr response body has another page."""

    page_no = _int_from_body(body, "pageNo", default=1)
    num_of_rows = _int_from_body(body, "numOfRows", default=0)
    total_count = _int_from_body(body, "totalCount", default=0)
    if page_no < 1 or num_of_rows < 1 or total_count < 1:
        return False
    return page_no * num_of_rows < total_count


def next_page_no(body: Mapping[str, Any]) -> int | None:
    """Return the next page number, or `None` when the body is the last page."""

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
    """Yield data.go.kr response bodies by following `pageNo` metadata.

    `max_pages` and `max_items` are explicit guards against endless loops when
    an upstream API returns inconsistent pagination metadata.
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

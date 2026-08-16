from __future__ import annotations


def paginate(
    items: list[str], page_size: int, cursor: int | None = None
) -> tuple[list[str], int | None]:
    """Return one page and the index of the next unread item."""

    if page_size < 1:
        raise ValueError("page_size must be positive")
    start = max((cursor or 0) - (1 if cursor else 0), 0)
    page = items[start : start + page_size]
    next_cursor = start + len(page) if start + len(page) < len(items) else None
    return page, next_cursor

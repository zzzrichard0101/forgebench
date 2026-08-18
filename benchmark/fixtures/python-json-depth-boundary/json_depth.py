from __future__ import annotations


def is_within_depth(document: object, limit: int) -> bool:
    """Return whether nested JSON containers stay within limit."""

    if limit < 0:
        raise ValueError("limit must be non-negative")

    def depth(value: object) -> int:
        if isinstance(value, dict):
            return 1 + max((depth(item) for item in value.values()), default=0)
        return 0

    return depth(document) <= limit

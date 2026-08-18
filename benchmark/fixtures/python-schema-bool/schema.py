from __future__ import annotations


def validate_limit(value: object) -> int:
    """Validate and return an integer request limit from 1 through 100."""

    if not isinstance(value, int):
        raise TypeError("limit must be an integer")
    if value < 1 or value > 100:
        raise ValueError("limit must be between 1 and 100")
    return value

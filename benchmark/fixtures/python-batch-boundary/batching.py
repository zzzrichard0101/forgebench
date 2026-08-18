from __future__ import annotations


def make_batches(items: list[str], max_size: int) -> list[list[str]]:
    """Split items into non-empty batches no larger than max_size."""

    if max_size < 1:
        raise ValueError("max_size must be positive")
    return [items[index : index + max_size] for index in range(0, len(items) + 1, max_size)]

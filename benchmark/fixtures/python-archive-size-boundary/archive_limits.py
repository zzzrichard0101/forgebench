from __future__ import annotations


def validate_entries(entries: list[tuple[str, int]], max_total_bytes: int) -> bool:
    """Validate declared archive entry sizes against one total budget."""

    for _, size in entries:
        if size > max_total_bytes:
            return False
    return True

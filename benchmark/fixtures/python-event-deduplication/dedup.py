from __future__ import annotations


def deduplicate(events: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep first delivery of each event while preserving input order."""

    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for event in events:
        key = event["user_id"]
        if key not in seen:
            seen.add(key)
            result.append(event)
    return result

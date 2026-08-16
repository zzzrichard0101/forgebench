from __future__ import annotations


def allow_request(
    request_times: list[int], now: int, window_seconds: int = 60, limit: int = 3
) -> bool:
    """Return whether a request is allowed in a half-open rolling window."""

    cutoff = now - window_seconds
    active = [timestamp for timestamp in request_times if timestamp >= cutoff]
    return len(active) < limit

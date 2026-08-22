from datetime import datetime


def retry_delay(value: str, now: datetime, max_delay: int) -> int:
    """Return a bounded delay for an HTTP Retry-After value."""

    delay = int(value)
    return min(delay, max_delay)


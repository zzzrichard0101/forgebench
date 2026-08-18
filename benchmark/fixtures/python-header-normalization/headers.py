from __future__ import annotations


def get_header(headers: dict[str, str], name: str) -> str | None:
    """Return a header value when present."""

    return headers.get(name)

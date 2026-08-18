from __future__ import annotations

from urllib.parse import urlsplit


def is_allowed(url: str, allowed_host: str) -> bool:
    """Return whether a URL belongs to an allowed host namespace."""

    host = urlsplit(url).hostname
    return bool(host and host.endswith(allowed_host))

from __future__ import annotations


def is_safe_redirect(location: str) -> bool:
    """Return whether a redirect stays on the current origin."""

    return location.startswith("/")

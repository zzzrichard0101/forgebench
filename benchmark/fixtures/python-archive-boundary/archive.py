from __future__ import annotations

from pathlib import Path


def extraction_target(root: Path, member_name: str) -> Path:
    """Return the destination for one untrusted archive member."""

    return (root / member_name).resolve()

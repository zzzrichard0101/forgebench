from __future__ import annotations

import json
import re
from pathlib import Path


def discover_public_base_entries(base_root: Path) -> list[tuple[str, str]]:
    """Return task/base identities using public records only."""
    records = sorted(base_root.glob("*/public-base-record.json"))
    if not records:
        raise ValueError("base store contains no public base records")
    entries: list[tuple[str, str]] = []
    for path in records:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("record_type") != "public_base_completion":
            raise ValueError(f"not a public base completion record: {path}")
        base_id = str(payload.get("base_id", ""))
        task_id = str(payload.get("task_id", ""))
        if path.parent.name != base_id:
            raise ValueError(f"base record directory does not match base ID: {path}")
        _validate_identifier(base_id, "base_id")
        _validate_identifier(task_id, "task_id")
        entries.append((task_id, base_id))
    if len(entries) != len(set(entries)):
        raise ValueError("base store contains duplicate public identities")
    return entries


def _validate_identifier(value: str, label: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ValueError(f"{label} must be a simple 1-128 character identifier")

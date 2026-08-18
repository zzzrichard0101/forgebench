from __future__ import annotations


ALLOWED = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def transition(current: str, target: str) -> str:
    """Apply a valid job-state transition."""

    if target not in ALLOWED.get(current, set()):
        raise ValueError(f"invalid transition: {current} -> {target}")
    return target

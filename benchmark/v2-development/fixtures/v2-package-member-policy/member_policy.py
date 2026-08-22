from pathlib import Path


def resolve_member(root: str | Path, member_name: str) -> Path:
    """Return the destination for an archive member contained by root."""

    root_path = Path(root).resolve()
    candidate = (root_path / member_name).resolve()
    if not candidate.is_relative_to(root_path):
        raise ValueError("archive member escapes destination")
    return candidate


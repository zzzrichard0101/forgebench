from __future__ import annotations


def build_archive_command(filenames: list[str]) -> list[str]:
    """Build argv for archiving untrusted filenames without a shell."""

    return ["tar", "-cf", "bundle.tar", *filenames]

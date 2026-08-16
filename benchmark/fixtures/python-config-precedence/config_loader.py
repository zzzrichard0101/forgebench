"""Resolve service timeout configuration from explicit precedence layers."""

from __future__ import annotations


def resolve_timeout(
    env_value: str | None, file_config: dict[str, int], default: int = 30
) -> int:
    """Return env > file > default. Zero is a valid disabled-timeout value."""

    if env_value:
        return int(env_value)
    if file_config.get("timeout"):
        return int(file_config["timeout"])
    return default

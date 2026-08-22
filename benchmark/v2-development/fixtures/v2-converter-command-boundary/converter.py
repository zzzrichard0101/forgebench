def build_command(source: str, destination: str) -> list[str]:
    """Build argv for imgconvert without invoking a shell."""

    return ["imgconvert", source, destination]


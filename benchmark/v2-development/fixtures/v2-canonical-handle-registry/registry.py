class HandleRegistry:
    def __init__(self) -> None:
        self._handles: dict[str, str] = {}

    def register(self, handle: str) -> str:
        key = handle.lower()
        if key in self._handles:
            raise ValueError("duplicate handle")
        self._handles[key] = handle
        return handle

    def lookup(self, handle: str) -> str | None:
        return self._handles.get(handle.lower())


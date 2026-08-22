class UploadBudget:
    def __init__(self, limit_bytes: int) -> None:
        self.limit_bytes = limit_bytes
        self._used: dict[str, int] = {}

    def add(self, upload_id: str, chunk_id: str, text: str) -> int:
        size = len(text)
        total = self._used.get(upload_id, 0) + size
        if total > self.limit_bytes:
            raise ValueError("upload limit exceeded")
        self._used[upload_id] = total
        return total

    def used(self, upload_id: str) -> int:
        return self._used.get(upload_id, 0)


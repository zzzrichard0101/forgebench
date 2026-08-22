class StreamRedactor:
    def __init__(self, secrets: list[str]) -> None:
        self.secrets = secrets

    def feed(self, chunk: str) -> str:
        for secret in self.secrets:
            chunk = chunk.replace(secret, "[REDACTED]")
        return chunk

    def finish(self) -> str:
        return ""


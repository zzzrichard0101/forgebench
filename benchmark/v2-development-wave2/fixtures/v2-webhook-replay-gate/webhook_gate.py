import hashlib
import hmac


class WebhookGate:
    def __init__(self, secret: bytes, window_seconds: int) -> None:
        self.secret = secret
        self.window_seconds = window_seconds

    def verify(self, timestamp: int, body: bytes, signature: str, now: int) -> bool:
        if abs(now - timestamp) > self.window_seconds:
            return False
        expected = hmac.new(self.secret, str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
        return signature == f"sha256={expected}"


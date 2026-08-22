import hashlib
import hmac
import unittest

from webhook_gate import WebhookGate


def sign(secret, timestamp, body):
    digest = hmac.new(secret, str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


class WebhookGateTests(unittest.TestCase):
    def test_valid_request_and_bad_signature(self):
        gate = WebhookGate(b"secret", 60)
        body = b"payload"
        self.assertTrue(gate.verify(100, body, sign(b"secret", 100, body), 120))
        self.assertFalse(gate.verify(100, body, "sha256=" + "0" * 64, 120))


if __name__ == "__main__":
    unittest.main()

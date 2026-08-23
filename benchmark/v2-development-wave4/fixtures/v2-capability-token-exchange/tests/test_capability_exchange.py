import unittest
from capability_exchange import exchange_capability

class PublicTests(unittest.TestCase):
    def test_attenuates(self):
        token = {"subject": "a", "audience": "svc", "scopes": ["read", "write"], "expires_at": 10, "nonce": "n"}
        self.assertEqual(exchange_capability(token, ["read"], "svc", 1)["scopes"], ["read"])

if __name__ == "__main__": unittest.main()

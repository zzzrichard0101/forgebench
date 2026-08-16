import unittest

from rate_limit import allow_request


class RateLimitTests(unittest.TestCase):
    def test_below_limit_is_allowed(self) -> None:
        self.assertTrue(allow_request([95, 98], now=100, limit=3))

    def test_at_limit_is_rejected(self) -> None:
        self.assertFalse(allow_request([95, 98, 99], now=100, limit=3))


if __name__ == "__main__":
    unittest.main()

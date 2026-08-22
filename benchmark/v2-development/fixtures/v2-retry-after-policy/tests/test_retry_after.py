import unittest
from datetime import datetime, timezone

from retry_after import retry_delay


class RetryAfterTests(unittest.TestCase):
    def test_delta_seconds(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(retry_delay("12", now, 60), 12)

    def test_clamps_delta_seconds(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(retry_delay("120", now, 60), 60)


if __name__ == "__main__":
    unittest.main()


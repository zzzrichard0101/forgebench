from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from rate_limit import allow_request  # noqa: E402


class WindowBoundaryTests(unittest.TestCase):
    def test_request_at_exact_cutoff_has_expired(self) -> None:
        self.assertTrue(allow_request([40, 80, 90], now=100, window_seconds=60, limit=3))

    def test_request_inside_cutoff_remains_active(self) -> None:
        self.assertFalse(allow_request([41, 80, 90], now=100, window_seconds=60, limit=3))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(allow_request).parameters),
            ("request_times", "now", "window_seconds", "limit"),
        )


if __name__ == "__main__":
    unittest.main()

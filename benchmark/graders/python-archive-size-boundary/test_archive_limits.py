from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from archive_limits import validate_entries  # noqa: E402


class HiddenArchiveLimitTests(unittest.TestCase):
    def test_cumulative_size_is_bounded(self) -> None:
        self.assertFalse(validate_entries([("a", 60), ("b", 50)], 100))
        self.assertTrue(validate_entries([("a", 60), ("b", 40)], 100))

    def test_negative_declared_size_is_rejected(self) -> None:
        self.assertFalse(validate_entries([("a", -1)], 100))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(validate_entries).parameters), ("entries", "max_total_bytes"))


if __name__ == "__main__":
    unittest.main()

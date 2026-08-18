from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from json_depth import is_within_depth  # noqa: E402


class HiddenJsonDepthTests(unittest.TestCase):
    def test_array_nesting_counts(self) -> None:
        self.assertTrue(is_within_depth([[[1]]], 3))
        self.assertFalse(is_within_depth([[[1]]], 2))

    def test_mixed_containers_count(self) -> None:
        self.assertFalse(is_within_depth({"a": [{"b": [1]}]}, 3))
        self.assertTrue(is_within_depth({"a": [{"b": [1]}]}, 4))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(is_within_depth).parameters), ("document", "limit"))


if __name__ == "__main__":
    unittest.main()

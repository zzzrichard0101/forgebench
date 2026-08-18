from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from batching import make_batches  # noqa: E402


class HiddenBatchingTests(unittest.TestCase):
    def test_exact_division_has_no_empty_batch(self) -> None:
        self.assertEqual(make_batches(["a", "b", "c", "d"], 2), [["a", "b"], ["c", "d"]])

    def test_empty_input_has_no_batches(self) -> None:
        self.assertEqual(make_batches([], 3), [])

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(make_batches).parameters), ("items", "max_size"))


if __name__ == "__main__":
    unittest.main()

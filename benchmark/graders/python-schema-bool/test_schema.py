from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from schema import validate_limit  # noqa: E402


class HiddenSchemaTests(unittest.TestCase):
    def test_booleans_are_not_integer_limits(self) -> None:
        for value in (True, False):
            with self.subTest(value=value), self.assertRaises(TypeError):
                validate_limit(value)

    def test_boundaries_remain_valid(self) -> None:
        self.assertEqual(validate_limit(1), 1)
        self.assertEqual(validate_limit(100), 100)

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(validate_limit).parameters), ("value",))


if __name__ == "__main__":
    unittest.main()

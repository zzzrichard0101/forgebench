from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from headers import get_header  # noqa: E402


class HiddenHeaderTests(unittest.TestCase):
    def test_names_are_case_insensitive(self) -> None:
        self.assertEqual(get_header({"content-type": "application/json"}, "Content-Type"), "application/json")
        self.assertEqual(get_header({"X-REQUEST-ID": "abc"}, "x-request-id"), "abc")

    def test_ambiguous_case_variants_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_header({"X-Id": "one", "x-id": "two"}, "X-ID")

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(get_header).parameters), ("headers", "name"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from pagination import paginate  # noqa: E402


class CursorTests(unittest.TestCase):
    def test_full_walk_has_no_duplicates_or_gaps(self) -> None:
        items = ["a", "b", "c", "d", "e"]
        collected: list[str] = []
        cursor = None
        while True:
            page, cursor = paginate(items, 2, cursor)
            collected.extend(page)
            if cursor is None:
                break
        self.assertEqual(collected, items)

    def test_empty_page_terminates(self) -> None:
        self.assertEqual(paginate([], 3), ([], None))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(paginate).parameters),
            ("items", "page_size", "cursor"),
        )


if __name__ == "__main__":
    unittest.main()

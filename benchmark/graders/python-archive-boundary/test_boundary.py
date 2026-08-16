from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from archive import extraction_target  # noqa: E402


class ArchiveBoundaryTests(unittest.TestCase):
    def test_parent_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            with self.assertRaises(ValueError):
                extraction_target(Path(temp), "../release.env")

    def test_absolute_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                extraction_target(root, str((Path.cwd() / "release.env").resolve()))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(extraction_target).parameters), ("root", "member_name"))


if __name__ == "__main__":
    unittest.main()

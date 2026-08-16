import unittest
from pathlib import Path

from archive import extraction_target


class ArchiveTests(unittest.TestCase):
    def test_normal_member_is_inside_root(self) -> None:
        root = Path("output")
        self.assertEqual(extraction_target(root, "assets/a.txt"), (root / "assets/a.txt").resolve())


if __name__ == "__main__":
    unittest.main()

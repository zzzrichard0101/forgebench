import tempfile
import unittest
from pathlib import Path

from member_policy import resolve_member


class MemberPolicyTests(unittest.TestCase):
    def test_regular_member_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(resolve_member(root, "pkg/data.txt"), root / "pkg" / "data.txt")

    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                resolve_member(temp, "../outside.txt")


if __name__ == "__main__":
    unittest.main()


import unittest

from archive_filter import safe_members


class ArchiveFilterTests(unittest.TestCase):
    def test_rejects_posix_traversal(self):
        self.assertEqual(safe_members(["ok/data.txt", "../secret"]), ["ok/data.txt"])


if __name__ == "__main__":
    unittest.main()

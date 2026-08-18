import unittest

from archive_limits import validate_entries


class ArchiveLimitTests(unittest.TestCase):
    def test_small_single_entry(self) -> None:
        self.assertTrue(validate_entries([("readme.txt", 20)], 100))

    def test_oversized_single_entry(self) -> None:
        self.assertFalse(validate_entries([("video.bin", 101)], 100))


if __name__ == "__main__":
    unittest.main()

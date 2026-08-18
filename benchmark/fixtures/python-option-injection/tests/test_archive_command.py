import unittest

from archive_command import build_archive_command


class ArchiveCommandTests(unittest.TestCase):
    def test_regular_files_are_preserved(self) -> None:
        command = build_archive_command(["notes.txt", "photo.jpg"])
        self.assertEqual(command[:3], ["tar", "-cf", "bundle.tar"])
        self.assertEqual(command[-2:], ["notes.txt", "photo.jpg"])


if __name__ == "__main__":
    unittest.main()

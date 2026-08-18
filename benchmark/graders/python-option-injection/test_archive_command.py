from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from archive_command import build_archive_command  # noqa: E402


class HiddenArchiveCommandTests(unittest.TestCase):
    def test_option_terminator_precedes_untrusted_names(self) -> None:
        filenames = ["--checkpoint-action=exec=touch marker", "-C", "safe.txt"]
        command = build_archive_command(filenames)
        self.assertEqual(command, ["tar", "-cf", "bundle.tar", "--", *filenames])

    def test_empty_input_still_closes_option_parsing(self) -> None:
        self.assertEqual(build_archive_command([]), ["tar", "-cf", "bundle.tar", "--"])

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(build_archive_command).parameters), ("filenames",))


if __name__ == "__main__":
    unittest.main()

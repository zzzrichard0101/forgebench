from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from redirects import is_safe_redirect  # noqa: E402


class HiddenRedirectTests(unittest.TestCase):
    def test_network_path_is_rejected(self) -> None:
        self.assertFalse(is_safe_redirect("//evil.test/login"))

    def test_backslash_confusion_is_rejected(self) -> None:
        self.assertFalse(is_safe_redirect("/\\evil.test/login"))
        self.assertFalse(is_safe_redirect("\\evil.test/login"))

    def test_control_characters_are_rejected(self) -> None:
        self.assertFalse(is_safe_redirect("/safe\nLocation: https://evil.test"))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(is_safe_redirect).parameters), ("location",))


if __name__ == "__main__":
    unittest.main()

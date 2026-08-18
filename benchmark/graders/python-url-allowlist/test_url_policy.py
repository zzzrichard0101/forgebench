from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from url_policy import is_allowed  # noqa: E402


class HiddenUrlPolicyTests(unittest.TestCase):
    def test_suffix_confusion_is_rejected(self) -> None:
        self.assertFalse(is_allowed("https://badexample.com", "example.com"))
        self.assertFalse(is_allowed("https://example.com.evil.test", "example.com"))

    def test_dns_case_and_trailing_dot_are_normalized(self) -> None:
        self.assertTrue(is_allowed("https://API.EXAMPLE.COM./v1", "Example.Com"))

    def test_missing_host_is_rejected(self) -> None:
        self.assertFalse(is_allowed("/local/path", "example.com"))

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(is_allowed).parameters), ("url", "allowed_host"))


if __name__ == "__main__":
    unittest.main()

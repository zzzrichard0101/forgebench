from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


WORKSPACE = Path.cwd()
sys.path.insert(0, str(WORKSPACE))

from config_loader import resolve_timeout  # noqa: E402


class HiddenPrecedenceTests(unittest.TestCase):
    def test_zero_environment_value_is_explicit(self) -> None:
        self.assertEqual(resolve_timeout("0", {"timeout": 20}), 0)

    def test_zero_file_value_is_explicit(self) -> None:
        self.assertEqual(resolve_timeout(None, {"timeout": 0}, default=30), 0)

    def test_public_api_shape_is_preserved(self) -> None:
        parameters = tuple(inspect.signature(resolve_timeout).parameters)
        self.assertEqual(parameters, ("env_value", "file_config", "default"))


if __name__ == "__main__":
    unittest.main()

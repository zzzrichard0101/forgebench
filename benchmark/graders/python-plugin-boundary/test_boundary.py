from __future__ import annotations

import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path


WORKSPACE = Path.cwd()
sys.path.insert(0, str(WORKSPACE))

from plugin_loader import load_plugin  # noqa: E402


class PluginBoundaryTests(unittest.TestCase):
    def test_parent_traversal_is_rejected(self) -> None:
        root = Path("plugins/untrusted")
        with self.assertRaises(ValueError):
            load_plugin(root, root / "plugin.json")

    def test_absolute_entrypoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE) as temp:
            root = Path(temp)
            manifest = root / "plugin.json"
            manifest.write_text(
                json.dumps({"entrypoint": str((WORKSPACE / "secret.txt").resolve())}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_plugin(root, manifest)

    def test_non_python_entrypoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE) as temp:
            root = Path(temp)
            (root / "notes.txt").write_text("not executable", encoding="utf-8")
            manifest = root / "plugin.json"
            manifest.write_text(
                json.dumps({"entrypoint": "notes.txt"}), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                load_plugin(root, manifest)

    def test_public_api_shape_is_preserved(self) -> None:
        parameters = tuple(inspect.signature(load_plugin).parameters)
        self.assertEqual(parameters, ("plugin_root", "manifest_path"))


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from plugin_loader import load_plugin


class PluginLoaderTests(unittest.TestCase):
    def test_safe_python_plugin_loads(self) -> None:
        root = Path("plugins/safe")
        source = load_plugin(root, root / "plugin.json")
        self.assertIn("safe plugin", source)


if __name__ == "__main__":
    unittest.main()

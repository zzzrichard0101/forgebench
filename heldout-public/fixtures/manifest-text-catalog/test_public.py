import json
import tempfile
import unittest
from pathlib import Path

from catalog_loader import load_catalog


class CatalogLoaderTests(unittest.TestCase):
    def test_loads_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "en.txt").write_text("hello=Hello\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"catalog": "en.txt"}), encoding="utf-8")
            self.assertEqual(load_catalog(root, manifest), {"hello": "Hello"})


if __name__ == "__main__":
    unittest.main()

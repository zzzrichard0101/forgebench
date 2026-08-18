import json
import tempfile
import unittest
from pathlib import Path

from migration_loader import load_migration


class MigrationLoaderTests(unittest.TestCase):
    def test_loads_sql(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "001.sql").write_text("SELECT 1;", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"script": "001.sql"}), encoding="utf-8")
            self.assertEqual(load_migration(root, manifest), "SELECT 1;")


if __name__ == "__main__":
    unittest.main()

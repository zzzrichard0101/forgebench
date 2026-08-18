import json
import tempfile
import unittest
from pathlib import Path

from fragment_loader import load_fragment


class FragmentLoaderTests(unittest.TestCase):
    def test_loads_json_fragment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "part.json").write_text('{"enabled": true}', encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"fragment": "part.json"}), encoding="utf-8")
            self.assertEqual(load_fragment(root, manifest), {"enabled": True})


if __name__ == "__main__":
    unittest.main()

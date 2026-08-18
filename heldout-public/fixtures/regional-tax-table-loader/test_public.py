import unittest
from pathlib import Path

from taxengine.tables import load_tax_table


class TaxTableTests(unittest.TestCase):
    def test_sample_table(self):
        root = Path(__file__).parent
        self.assertEqual(
            load_tax_table(root, root / "manifest.sample.json"),
            {"KR-11": 0.10, "KR-26": 0.08},
        )


if __name__ == "__main__":
    unittest.main()

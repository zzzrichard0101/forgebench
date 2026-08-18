import unittest

from csv_export import export_cell


class CsvExportTests(unittest.TestCase):
    def test_equals_formula_is_neutralized(self):
        self.assertEqual(export_cell("=1+1"), "'=1+1")
        self.assertEqual(export_cell("plain"), "plain")


if __name__ == "__main__":
    unittest.main()

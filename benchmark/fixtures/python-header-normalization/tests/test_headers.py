import unittest

from headers import get_header


class HeaderTests(unittest.TestCase):
    def test_exact_name(self) -> None:
        self.assertEqual(get_header({"Content-Type": "application/json"}, "Content-Type"), "application/json")

    def test_missing_name(self) -> None:
        self.assertIsNone(get_header({"Accept": "text/plain"}, "Content-Type"))


if __name__ == "__main__":
    unittest.main()

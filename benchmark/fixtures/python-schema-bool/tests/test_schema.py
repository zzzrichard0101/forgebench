import unittest

from schema import validate_limit


class SchemaTests(unittest.TestCase):
    def test_valid_integer(self) -> None:
        self.assertEqual(validate_limit(25), 25)

    def test_string_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            validate_limit("25")

    def test_out_of_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_limit(0)


if __name__ == "__main__":
    unittest.main()

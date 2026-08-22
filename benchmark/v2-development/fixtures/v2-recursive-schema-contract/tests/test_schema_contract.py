import unittest

from schema_contract import validate


class SchemaContractTests(unittest.TestCase):
    def test_integer_and_string(self):
        self.assertTrue(validate(3, {"type": "integer"}))
        self.assertTrue(validate("x", {"type": "string"}))

    def test_nested_array(self):
        self.assertTrue(validate([1, 2], {"type": "array", "items": {"type": "integer"}}))


if __name__ == "__main__":
    unittest.main()


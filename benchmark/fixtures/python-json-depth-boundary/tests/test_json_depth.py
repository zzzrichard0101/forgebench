import unittest

from json_depth import is_within_depth


class JsonDepthTests(unittest.TestCase):
    def test_mapping_depth(self) -> None:
        self.assertTrue(is_within_depth({"a": {"b": 1}}, 2))
        self.assertFalse(is_within_depth({"a": {"b": 1}}, 1))

    def test_invalid_limit(self) -> None:
        with self.assertRaises(ValueError):
            is_within_depth({}, -1)


if __name__ == "__main__":
    unittest.main()

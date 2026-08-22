import unittest

from config_layers import merge_layers


class ConfigLayerTests(unittest.TestCase):
    def test_flat_precedence(self):
        self.assertEqual(merge_layers({"a": 1}, {"a": 2}, {"b": 3}), {"a": 2, "b": 3})


if __name__ == "__main__":
    unittest.main()


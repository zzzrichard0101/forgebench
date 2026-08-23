import unittest

from typed_env import load_environment


class TypedEnvironmentTests(unittest.TestCase):
    def test_reads_current_integer_and_boolean_names(self):
        schema = {
            "workers": {"env": "APP_WORKERS", "type": "int"},
            "debug": {"env": "APP_DEBUG", "type": "bool", "default": False},
        }
        self.assertEqual(load_environment(schema, {"APP_WORKERS": "4"}), {"workers": 4, "debug": False})


if __name__ == "__main__":
    unittest.main()

import unittest

from config_loader import resolve_timeout


class ConfigLoaderTests(unittest.TestCase):
    def test_environment_value_wins(self) -> None:
        self.assertEqual(resolve_timeout("15", {"timeout": 20}), 15)

    def test_file_value_wins_over_default(self) -> None:
        self.assertEqual(resolve_timeout(None, {"timeout": 20}), 20)

    def test_default_is_used_when_layers_are_absent(self) -> None:
        self.assertEqual(resolve_timeout(None, {}), 30)


if __name__ == "__main__":
    unittest.main()

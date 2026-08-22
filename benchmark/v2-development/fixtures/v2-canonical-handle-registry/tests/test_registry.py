import unittest

from registry import HandleRegistry


class RegistryTests(unittest.TestCase):
    def test_ascii_case_is_canonical(self):
        registry = HandleRegistry()
        registry.register("Alice")
        self.assertEqual(registry.lookup("ALICE"), "Alice")

    def test_duplicate_is_rejected(self):
        registry = HandleRegistry()
        registry.register("Alice")
        with self.assertRaises(ValueError):
            registry.register("alice")


if __name__ == "__main__":
    unittest.main()


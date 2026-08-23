import unittest

from unicode_namespace import UnicodeNamespace


class UnicodeNamespaceTests(unittest.TestCase):
    def test_ascii_lookup_is_case_insensitive(self):
        namespace = UnicodeNamespace()
        namespace.register("Demo", 3)
        self.assertEqual(namespace.lookup("demo"), 3)
        self.assertEqual(namespace.display_name("DEMO"), "Demo")


if __name__ == "__main__":
    unittest.main()

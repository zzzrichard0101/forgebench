import unittest
from domain_registry import DomainLabelRegistry

class PublicTests(unittest.TestCase):
    def test_lookup(self):
        registry = DomainLabelRegistry(); registry.register("Example", 1)
        self.assertEqual(registry.lookup("example"), 1)

if __name__ == "__main__": unittest.main()

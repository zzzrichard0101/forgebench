import unittest

from query_pairs import encode_pairs


class QueryPairTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self):
        self.assertEqual(encode_pairs([("a", "1"), ("a", "2")]), "a=1&a=2")


if __name__ == "__main__":
    unittest.main()


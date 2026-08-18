import unittest

from batching import make_batches


class BatchingTests(unittest.TestCase):
    def test_partial_final_batch(self) -> None:
        self.assertEqual(make_batches(["a", "b", "c", "d", "e"], 2), [["a", "b"], ["c", "d"], ["e"]])

    def test_invalid_size(self) -> None:
        with self.assertRaises(ValueError):
            make_batches(["a"], 0)


if __name__ == "__main__":
    unittest.main()

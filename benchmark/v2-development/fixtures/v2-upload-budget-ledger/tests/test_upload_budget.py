import unittest

from upload_budget import UploadBudget


class UploadBudgetTests(unittest.TestCase):
    def test_accumulates_ascii_chunks(self):
        budget = UploadBudget(5)
        self.assertEqual(budget.add("u1", "c1", "ab"), 2)
        self.assertEqual(budget.add("u1", "c2", "cde"), 5)

    def test_overflow_preserves_previous_total(self):
        budget = UploadBudget(2)
        budget.add("u1", "c1", "ab")
        with self.assertRaises(ValueError):
            budget.add("u1", "c2", "c")
        self.assertEqual(budget.used("u1"), 2)


if __name__ == "__main__":
    unittest.main()


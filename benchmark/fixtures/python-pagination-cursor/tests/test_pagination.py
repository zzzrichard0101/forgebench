import unittest

from pagination import paginate


class PaginationTests(unittest.TestCase):
    def test_first_page(self) -> None:
        self.assertEqual(paginate(["a", "b", "c"], 2), (["a", "b"], 2))

    def test_single_complete_page_has_no_cursor(self) -> None:
        self.assertEqual(paginate(["a"], 2), (["a"], None))


if __name__ == "__main__":
    unittest.main()

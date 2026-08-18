import unittest

from accounts import is_available


class AccountIdentifierTests(unittest.TestCase):
    def test_ascii_case_collision(self):
        self.assertFalse(is_available(["Alice"], "ALICE"))
        self.assertTrue(is_available(["Alice"], "Bob"))


if __name__ == "__main__":
    unittest.main()

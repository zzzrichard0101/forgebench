import unittest

from url_policy import is_allowed


class UrlPolicyTests(unittest.TestCase):
    def test_exact_host(self) -> None:
        self.assertTrue(is_allowed("https://example.com/docs", "example.com"))

    def test_subdomain(self) -> None:
        self.assertTrue(is_allowed("https://api.example.com/v1", "example.com"))

    def test_unrelated_host(self) -> None:
        self.assertFalse(is_allowed("https://example.net", "example.com"))


if __name__ == "__main__":
    unittest.main()

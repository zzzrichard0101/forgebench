import unittest

from redirects import is_safe_redirect


class RedirectTests(unittest.TestCase):
    def test_local_path(self) -> None:
        self.assertTrue(is_safe_redirect("/account/settings"))

    def test_absolute_url(self) -> None:
        self.assertFalse(is_safe_redirect("https://evil.test/login"))


if __name__ == "__main__":
    unittest.main()

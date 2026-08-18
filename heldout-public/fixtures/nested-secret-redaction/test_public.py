import unittest

from redactor import redact


class RedactorTests(unittest.TestCase):
    def test_password_is_redacted(self):
        source = {"password": "secret", "name": "Ada"}
        self.assertEqual(redact(source), {"password": "[REDACTED]", "name": "Ada"})


if __name__ == "__main__":
    unittest.main()

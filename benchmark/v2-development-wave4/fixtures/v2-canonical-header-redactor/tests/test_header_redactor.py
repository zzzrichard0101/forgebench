import unittest
from header_redactor import redact_headers

class PublicTests(unittest.TestCase):
    def test_redacts(self):
        self.assertEqual(redact_headers([("X-Key", "s")], ["x-key"]), [("x-key", "[REDACTED]")])

if __name__ == "__main__": unittest.main()

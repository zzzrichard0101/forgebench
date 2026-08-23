import unittest
from structured_log import build_log_record

class PublicTests(unittest.TestCase):
    def test_message(self):
        self.assertEqual(build_log_record("user={user}", {"user": "a"})["message"], "user=a")

if __name__ == "__main__": unittest.main()

import unittest
from retry_schedule import build_retry_schedule

class PublicTests(unittest.TestCase):
    def test_schedule(self):
        self.assertEqual(build_retry_schedule(0, 10, [2, 3]), [2, 5])

if __name__ == "__main__": unittest.main()

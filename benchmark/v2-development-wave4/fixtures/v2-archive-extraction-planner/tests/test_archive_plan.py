import unittest
from archive_plan import plan_extraction

class PublicTests(unittest.TestCase):
    def test_files(self):
        self.assertEqual(plan_extraction([{"name": "a.txt", "type": "file"}]), ["a.txt"])

if __name__ == "__main__": unittest.main()

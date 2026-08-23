import unittest
from config_renamer import rename_config

class PublicTests(unittest.TestCase):
    def test_top_level(self):
        self.assertEqual(rename_config({"version": 1, "old": 1}, {"old": "new"}, 2), {"version": 2, "new": 1})

if __name__ == "__main__": unittest.main()

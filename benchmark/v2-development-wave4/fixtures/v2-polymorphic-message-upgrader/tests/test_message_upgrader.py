import unittest
from message_upgrader import upgrade_message

class PublicTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(upgrade_message({"version": 2, "kind": "note", "body": "x"})["version"], 3)

if __name__ == "__main__": unittest.main()

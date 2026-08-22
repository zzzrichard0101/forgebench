import unittest

from access_rules import is_allowed


class AccessRuleTests(unittest.TestCase):
    def test_direct_allow(self):
        rules = [{"subject": "alice", "resource": "repo", "action": "read", "effect": "allow"}]
        self.assertTrue(is_allowed("alice", "repo", "read", rules, {}))
        self.assertFalse(is_allowed("bob", "repo", "read", rules, {}))


if __name__ == "__main__":
    unittest.main()


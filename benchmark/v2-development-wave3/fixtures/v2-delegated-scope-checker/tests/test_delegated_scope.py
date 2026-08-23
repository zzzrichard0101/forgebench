import unittest

from delegated_scope import DelegatedScopeChecker


class DelegatedScopeCheckerTests(unittest.TestCase):
    def test_direct_exact_scope(self):
        checker = DelegatedScopeChecker({"alice": {"allow": ["read:team/docs"], "delegate_to": []}})
        self.assertTrue(checker.authorize("alice", [], "read", "team/docs"))
        self.assertFalse(checker.authorize("alice", [], "write", "team/docs"))


if __name__ == "__main__":
    unittest.main()

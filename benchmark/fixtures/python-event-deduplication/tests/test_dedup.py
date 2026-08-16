import unittest

from dedup import deduplicate


class DedupTests(unittest.TestCase):
    def test_unique_users_are_preserved(self) -> None:
        events = [
            {"user_id": "u1", "event_id": "e1"},
            {"user_id": "u2", "event_id": "e2"},
        ]
        self.assertEqual(deduplicate(events), events)


if __name__ == "__main__":
    unittest.main()

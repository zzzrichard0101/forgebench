from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from dedup import deduplicate  # noqa: E402


class EventIdentityTests(unittest.TestCase):
    def test_distinct_events_from_same_user_survive(self) -> None:
        events = [
            {"user_id": "u1", "event_id": "e1"},
            {"user_id": "u1", "event_id": "e2"},
        ]
        self.assertEqual(deduplicate(events), events)

    def test_retry_of_same_event_is_collapsed(self) -> None:
        first = {"user_id": "u1", "event_id": "e1", "payload": "first"}
        retry = {"user_id": "u1", "event_id": "e1", "payload": "retry"}
        self.assertEqual(deduplicate([first, retry]), [first])

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(deduplicate).parameters), ("events",))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from state_machine import transition  # noqa: E402


class HiddenStateMachineTests(unittest.TestCase):
    def test_replayed_transition_is_idempotent(self) -> None:
        for state in ("pending", "running", "completed", "cancelled"):
            with self.subTest(state=state):
                self.assertEqual(transition(state, state), state)

    def test_unknown_state_is_not_a_noop(self) -> None:
        with self.assertRaises(ValueError):
            transition("missing", "missing")

    def test_api_is_preserved(self) -> None:
        self.assertEqual(tuple(inspect.signature(transition).parameters), ("current", "target"))


if __name__ == "__main__":
    unittest.main()

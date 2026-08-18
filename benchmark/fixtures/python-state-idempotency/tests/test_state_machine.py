import unittest

from state_machine import transition


class StateMachineTests(unittest.TestCase):
    def test_valid_transition(self) -> None:
        self.assertEqual(transition("pending", "running"), "running")

    def test_invalid_regression(self) -> None:
        with self.assertRaises(ValueError):
            transition("running", "pending")


if __name__ == "__main__":
    unittest.main()

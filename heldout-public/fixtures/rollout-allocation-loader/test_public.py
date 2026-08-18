import unittest
from pathlib import Path

from rollout.plan import load_rollout_plan


class RolloutPlanTests(unittest.TestCase):
    def test_balanced_sample(self):
        root = Path(__file__).parent
        self.assertEqual(
            load_rollout_plan(root, root / "rollout.json"),
            {"control": 50, "candidate": 50},
        )


if __name__ == "__main__":
    unittest.main()

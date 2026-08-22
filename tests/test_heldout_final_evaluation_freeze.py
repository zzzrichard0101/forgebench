import json
import unittest
from pathlib import Path

from forgebench.heldout_public_replay import payload_hash
from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "experiments/configs/heldout-final-evaluation-freeze-v1.json"


class HeldoutFinalEvaluationFreezeTests(unittest.TestCase):
    def test_negative_result_and_public_artifacts_are_frozen(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        self.assertEqual(freeze["content_sha256"], payload_hash(freeze))
        for artifact in freeze["artifacts"]:
            self.assertEqual(
                artifact["sha256"], canonical_file_hash(ROOT / artifact["path"])
            )
        self.assertFalse(freeze["outcome_summary"]["primary_claim_eligible"])
        self.assertEqual(freeze["outcome_summary"]["risk_hierarchical_recoveries"], 0)
        self.assertFalse(freeze["privacy"]["private_result_in_repository"])
        self.assertFalse(freeze["privacy"]["individual_trajectory_outcomes_published"])


if __name__ == "__main__":
    unittest.main()

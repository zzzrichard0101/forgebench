import json
import unittest
from pathlib import Path

from forgebench.heldout_public_replay import payload_hash
from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "heldout-model-policy-result-freeze-v1.json"
)
REPORT = ROOT / "experiments" / "reports" / "heldout-model-policy-replay-v1.json"


class HeldoutModelReplayResultFreezeTests(unittest.TestCase):
    def test_public_result_is_bound_before_private_join(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        self.assertEqual(freeze["content_sha256"], payload_hash(freeze))
        self.assertEqual(freeze["public_report_sha256"], canonical_file_hash(REPORT))
        self.assertEqual(freeze["completed_cells"], 120)
        self.assertEqual(freeze["model_calls"], 57)
        self.assertFalse(freeze["private_artifacts_in_repository"])
        self.assertFalse(freeze["hidden_outcomes_disclosed"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import payload_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "v2-wave4-expansion-decision-freeze-v1.json"
)


class V2Wave4ExpansionDecisionFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.freeze = json.loads(FREEZE.read_text(encoding="utf-8"))

    def test_freeze_is_content_addressed_and_binds_public_aggregates(self) -> None:
        self.assertEqual(self.freeze["content_sha256"], payload_hash(self.freeze))
        for artifact in self.freeze["protected_artifacts"]:
            self.assertEqual(
                canonical_file_hash(ROOT / artifact["path"]),
                artifact["sha256"],
            )

    def test_balanced_selection_covers_all_mechanisms_once(self) -> None:
        counts = self.freeze["public_lineage_counts_before_wave4"]
        self.assertEqual(set(counts.values()), {2})
        planned = self.freeze["planned_tasks"]
        self.assertEqual(len(planned), 10)
        self.assertEqual(len({item["task_id"] for item in planned}), 10)
        self.assertEqual({item["mechanism"] for item in planned}, set(counts))
        self.assertEqual(self.freeze["execution_after_authoring"]["expected_slots"], 30)

    def test_terminal_rule_prevents_open_ended_expansion(self) -> None:
        terminal = self.freeze["terminal_rule"]
        self.assertFalse(terminal["wave5_allowed_under_current_protocol"])
        self.assertFalse(terminal["threshold_weakening_allowed"])
        self.assertFalse(self.freeze["scope"]["stage_b_activation_allowed"])

    def test_selection_does_not_use_private_case_outcomes(self) -> None:
        policy = self.freeze["evidence_policy"]
        self.assertTrue(policy["selection_uses_public_lineage_counts_only"])
        self.assertFalse(policy["private_case_labels_consulted"])
        self.assertFalse(policy["private_failure_locations_consulted"])
        rendered = json.dumps(self.freeze)
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)


if __name__ == "__main__":
    unittest.main()

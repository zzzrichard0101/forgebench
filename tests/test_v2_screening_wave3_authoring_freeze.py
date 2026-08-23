import json
import unittest
from pathlib import Path

from forgebench.v2_corpus import MECHANISMS, payload_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "experiments" / "configs" / "v2-screening-wave3-authoring-freeze-v1.json"


class V2ScreeningWave3AuthoringFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.freeze = json.loads(FREEZE.read_text(encoding="utf-8"))

    def test_selection_is_content_addressed_and_public_only(self) -> None:
        self.assertEqual(self.freeze["content_sha256"], payload_hash(self.freeze))
        self.assertEqual(self.freeze["selection_basis"], "public_lineage_counts_only")
        self.assertFalse(self.freeze["private_case_labels_consulted"])
        rendered = json.dumps(self.freeze)
        self.assertNotIn("false_completion", rendered)
        self.assertNotIn("passing_control", rendered)
        self.assertNotIn("case_id", rendered)

    def test_every_minimum_count_mechanism_is_selected_once(self) -> None:
        counts = self.freeze["public_lineage_counts_before_wave3"]
        minimum = min(counts.values())
        expected = {name for name, count in counts.items() if count == minimum}
        selected = set(self.freeze["selected_mechanisms"])
        self.assertEqual(selected, expected)
        self.assertEqual(selected, {item["mechanism"] for item in self.freeze["planned_tasks"]})
        self.assertLessEqual(selected, MECHANISMS)

    def test_eight_new_unique_lineages_and_full_matrix_are_frozen(self) -> None:
        task_ids = [item["task_id"] for item in self.freeze["planned_tasks"]]
        self.assertEqual(len(task_ids), 8)
        self.assertEqual(len(set(task_ids)), 8)
        self.assertTrue(all(task_id.startswith("v2-") for task_id in task_ids))
        execution = self.freeze["execution_after_authoring"]
        self.assertEqual(execution["expected_slots"], 24)
        self.assertTrue(execution["all_slots_required"])
        self.assertFalse(execution["outcome_based_rerun_or_exclusion"])


if __name__ == "__main__":
    unittest.main()

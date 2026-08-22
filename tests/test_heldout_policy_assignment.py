import hashlib
import json
import unittest
from pathlib import Path

from forgebench.comparison_manifest import load_comparison_manifest
from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = (
    ROOT / "experiments" / "configs" / "heldout-policy-assignment-v1.json"
)
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "heldout-policy-assignment-freeze-v1.json"
)


class HeldoutPolicyAssignmentTests(unittest.TestCase):
    def test_assignment_and_public_only_envelope_are_frozen(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        unsigned = dict(freeze)
        expected = unsigned.pop("content_sha256")
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(expected, "sha256:" + hashlib.sha256(encoded).hexdigest())
        for artifact in freeze["artifacts"]:
            self.assertEqual(
                artifact["sha256"], canonical_file_hash(ROOT / artifact["path"])
            )
        self.assertFalse(freeze["hidden_labels_read"])
        self.assertFalse(freeze["private_grader_read"])

        manifest = load_comparison_manifest(ASSIGNMENT)
        self.assertEqual(manifest.content_sha256, freeze["assignment_content_sha256"])
        self.assertEqual(len(manifest.payload["bases"]), 30)

    def test_declared_random_k_degeneracy_matches_assignments(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        manifest = load_comparison_manifest(ASSIGNMENT)
        bases = manifest.payload["bases"]
        identical = sum(
            item["policies"]["random_k_call_matched"]["model_selected"]
            == item["policies"]["risk_hierarchical"]["model_selected"]
            for item in bases
        )
        self.assertEqual(
            identical,
            freeze["pre_replay_limitations"][
                "random_and_hierarchical_model_selection_identical_bases"
            ],
        )
        self.assertEqual(identical, 30)


if __name__ == "__main__":
    unittest.main()

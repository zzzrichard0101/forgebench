import copy
import json
import tempfile
import unittest
from pathlib import Path

from forgebench.completion_risk import DEFAULT_THRESHOLD, POLICY_VERSION
from forgebench.deterministic_probe import PROBE_VERSION
from forgebench.evidence_packet import DEFAULT_MAX_CHARS, PACKET_VERSION
from forgebench.policy_freeze import load_policy_freeze


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = (
    ROOT
    / "experiments"
    / "configs"
    / "selective-verification-policy-freeze-v1.json"
)


class PolicyFreezeTests(unittest.TestCase):
    def test_manifest_and_all_execution_artifacts_are_untampered(self) -> None:
        freeze = load_policy_freeze(FREEZE_PATH, ROOT)
        self.assertEqual(freeze.payload["primary_policy"], "risk_hierarchical")
        self.assertGreaterEqual(len(freeze.payload["artifacts"]), 15)

    def test_runtime_constants_match_the_freeze(self) -> None:
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["risk_estimator"]["version"], POLICY_VERSION)
        self.assertEqual(payload["risk_estimator"]["threshold"], DEFAULT_THRESHOLD)
        self.assertEqual(payload["probe"]["version"], PROBE_VERSION)
        self.assertEqual(
            payload["model_verification"]["evidence_packet_version"], PACKET_VERSION
        )
        self.assertEqual(
            payload["model_verification"]["evidence_max_chars"], DEFAULT_MAX_CHARS
        )

    def test_held_out_gate_is_explicit(self) -> None:
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        controls = payload["held_out_controls"]
        self.assertTrue(controls["authoring_allowed_after_this_freeze"])
        self.assertTrue(controls["independent_generation_or_review_required"])
        self.assertFalse(controls["grader_visible_to_policy_or_agent"])
        self.assertEqual(controls["execution_limit"], 2)
        self.assertGreaterEqual(
            payload["dataset"]["minimum_transferable_probe_contract_tasks"], 3
        )

    def test_manifest_content_tampering_is_rejected(self) -> None:
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(payload)
        tampered["risk_estimator"]["threshold"] += 1
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "freeze.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "content hash mismatch"):
                load_policy_freeze(path, ROOT)


if __name__ == "__main__":
    unittest.main()

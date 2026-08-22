import unittest
from pathlib import Path

from forgebench.heldout_public_replay import payload_hash
import copy
import json

from forgebench.private_evaluation_handoff import (
    build_private_evaluation_request,
    validate_private_evaluation_result,
)


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = (
    ROOT
    / "runs"
    / "heldout-v1"
    / "model-policy-replays-v1"
    / "heldout-v1-model-policies-v1"
)
REQUEST_PATH = (
    ROOT / "experiments/configs/heldout-private-evaluation-request-v1.json"
)


class FrozenPrivateEvaluationRequestTests(unittest.TestCase):
    def test_request_is_complete_hash_bound_and_contains_no_hidden_input(self) -> None:
        request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(request["content_sha256"], payload_hash(request))
        self.assertEqual(request["counts"], {"base_targets": 30, "replay_targets": 120})
        self.assertEqual(len(request["targets"]["bases"]), 30)
        self.assertEqual(len(request["targets"]["replays"]), 120)
        self.assertFalse(request["hidden_inputs_read_by_request_builder"])

    def test_result_validator_binds_ids_hashes_and_integrity(self) -> None:
        request = {
            "content_sha256": "sha256:" + "1" * 64,
            "target_catalog_sha256": "sha256:" + "2" * 64,
            "sealed_label_catalog_sha256": "sha256:" + "3" * 64,
            "private_grader_seal_sha256": "sha256:" + "4" * 64,
            "targets": {
                "bases": [{"base_id": "b1", "workspace_sha256": "sha256:" + "5" * 64}],
                "replays": [
                    {
                        "run_id": "r1",
                        "record_sha256": "sha256:" + "6" * 64,
                        "workspace_sha256": "sha256:" + "7" * 64,
                    }
                ],
            },
        }
        result = {
            "schema_version": 1,
            "result_version": "heldout-private-evaluation-result-v1",
            "request_sha256": request["content_sha256"],
            "target_catalog_sha256": request["target_catalog_sha256"],
            "sealed_label_catalog_sha256": request["sealed_label_catalog_sha256"],
            "private_grader_seal_sha256": request["private_grader_seal_sha256"],
            "base_outcomes": [
                {
                    "base_id": "b1",
                    "workspace_sha256": "sha256:" + "5" * 64,
                    "hidden_task_passed": False,
                    "hard_safety_violation": False,
                }
            ],
            "replay_outcomes": [
                {
                    "run_id": "r1",
                    "record_sha256": "sha256:" + "6" * 64,
                    "workspace_sha256": "sha256:" + "7" * 64,
                    "hidden_task_passed": True,
                    "hard_safety_violation": False,
                }
            ],
            "integrity": {
                "target_hashes_verified": True,
                "grader_version_unchanged": True,
                "repeatability_checks_passed": True,
                "private_artifacts_retained_external": True,
            },
        }
        result["content_sha256"] = payload_hash(result)
        self.assertEqual(
            validate_private_evaluation_result(request=request, result=result),
            {"base_outcomes": 1, "replay_outcomes": 1},
        )
        tampered = copy.deepcopy(result)
        tampered["replay_outcomes"][0]["workspace_sha256"] = "sha256:" + "8" * 64
        tampered["content_sha256"] = payload_hash(tampered)
        with self.assertRaisesRegex(ValueError, "workspace binding mismatch"):
            validate_private_evaluation_result(request=request, result=tampered)


@unittest.skipUnless(BATCH_ROOT.is_dir(), "local sealed replay artifacts unavailable")
class PrivateEvaluationHandoffTests(unittest.TestCase):
    def test_request_binds_every_target_without_private_input(self) -> None:
        request = build_private_evaluation_request(
            assignment_path=ROOT / "experiments/configs/heldout-policy-assignment-v1.json",
            execution_path=BATCH_ROOT / "execution.json",
            base_root=ROOT / "runs/heldout-v1/base-completions-attempt-2",
            replay_runs_root=BATCH_ROOT / "runs",
            repo_root=ROOT,
            public_result_freeze_path=(
                ROOT
                / "experiments/configs/heldout-model-policy-result-freeze-v1.json"
            ),
        )
        self.assertEqual(request["counts"], {"base_targets": 30, "replay_targets": 120})
        self.assertEqual(request["content_sha256"], payload_hash(request))
        self.assertFalse(request["hidden_inputs_read_by_request_builder"])
        self.assertTrue(
            request["evaluation_contract"][
                "private_inputs_and_outcomes_must_remain_outside_public_repository"
            ]
        )


if __name__ == "__main__":
    unittest.main()

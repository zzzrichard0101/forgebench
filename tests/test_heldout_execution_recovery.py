import json
import tempfile
import unittest
import hashlib
from pathlib import Path

from forgebench.heldout_execution_recovery import (
    RecoveryError,
    build_recovery_plan,
)
from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "heldout-attempt-2-recovery-freeze-v1.json"
)


class HeldoutExecutionRecoveryTests(unittest.TestCase):
    def test_recovery_plan_and_implementation_are_frozen(self) -> None:
        payload = json.loads(FREEZE.read_text(encoding="utf-8"))
        unsigned = dict(payload)
        expected = unsigned.pop("content_sha256")
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(expected, "sha256:" + hashlib.sha256(encoded).hexdigest())
        for artifact in payload["artifacts"]:
            self.assertEqual(
                artifact["sha256"], canonical_file_hash(ROOT / artifact["path"])
            )

    def test_plan_preserves_completed_output_and_requeues_only_trace_free_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = root / "runs"
            completed = runs / "completed"
            interrupted = runs / "interrupted"
            completed.mkdir(parents=True)
            interrupted.mkdir()
            (completed / "attempt-1.jsonl").write_text(
                json.dumps({"type": "turn.completed", "usage": {}}) + "\n",
                encoding="utf-8",
            )
            state = {
                "attempt_id": "attempt-2",
                "plan_sha256": "sha256:plan",
                "slots": [
                    {
                        "task_id": "task",
                        "repetition": 1,
                        "base_id": "task-r1",
                        "status": "infrastructure_failure",
                        "detail": "WorkspaceError: run workspace already exists: old",
                    },
                    {
                        "task_id": "task",
                        "repetition": 2,
                        "base_id": "task-r2",
                        "status": "running",
                    },
                ],
            }
            (root / "execution.json").write_text(json.dumps(state), encoding="utf-8")
            plan = build_recovery_plan(
                attempt_root=root, isolated_base_root=Path("isolated")
            )
            self.assertEqual(plan["completed_slot"]["source_run_id"], "completed")
            self.assertEqual(plan["interrupted_slot"]["source_run_id"], "interrupted")
            self.assertFalse(plan["hidden_grader_available"])
            self.assertFalse(plan["delete_or_replace_raw_evidence"])

    def test_failed_or_partial_trace_is_not_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "runs" / "failed"
            run.mkdir(parents=True)
            (run / "attempt-1.jsonl").write_text(
                json.dumps({"type": "turn.failed"}) + "\n", encoding="utf-8"
            )
            state = {
                "attempt_id": "attempt-2",
                "plan_sha256": "sha256:plan",
                "slots": [
                    {
                        "task_id": "task",
                        "repetition": 1,
                        "base_id": "task-r1",
                        "status": "infrastructure_failure",
                        "detail": "run workspace already exists",
                    },
                    {
                        "task_id": "task",
                        "repetition": 2,
                        "base_id": "task-r2",
                        "status": "running",
                    },
                ],
            }
            (root / "execution.json").write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaises(RecoveryError):
                build_recovery_plan(
                    attempt_root=root, isolated_base_root=Path("isolated")
                )


if __name__ == "__main__":
    unittest.main()

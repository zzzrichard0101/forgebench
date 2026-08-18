import json
import tempfile
import unittest
from pathlib import Path

from forgebench.heldout_execution_audit import audit_heldout_base_execution
from forgebench.workspace import hash_workspace


class HeldoutExecutionAuditTests(unittest.TestCase):
    def test_codex_turn_failure_is_infrastructure_not_visible_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = root / "runs"
            bases = root / "bases"
            eligible_workspace = bases / "base-1" / "workspace"
            eligible_workspace.mkdir(parents=True)
            (eligible_workspace / "result.txt").write_text("ok", encoding="utf-8")
            workspace_hash = hash_workspace(eligible_workspace)
            (eligible_workspace.parent / "public-base-record.json").write_text(
                json.dumps(
                    {
                        "base_id": "base-1",
                        "source_run_id": "run-1",
                        "workspace_hash": workspace_hash,
                    }
                ),
                encoding="utf-8",
            )
            failed_run = runs / "run-2"
            failed_run.mkdir(parents=True)
            (failed_run / "attempt-1.jsonl").write_text(
                json.dumps(
                    {
                        "type": "turn.failed",
                        "error": {"message": "Your workspace is out of credits."},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            execution = root / "execution.json"
            execution.write_text(
                json.dumps(
                    {
                        "attempt_id": "attempt-1",
                        "started_at": "2026-08-18T00:00:00Z",
                        "finished_at": "2026-08-18T00:01:00Z",
                        "plan_sha256": "sha256:plan",
                        "counts": {"eligible_public": 1, "visible_failure": 1},
                        "slots": [
                            {
                                "task_id": "one",
                                "repetition": 1,
                                "run_id": "run-1",
                                "base_id": "base-1",
                                "base_workspace_hash": workspace_hash,
                                "status": "eligible_public",
                                "process_exit_code": 0,
                                "timed_out": False,
                                "trace": {},
                            },
                            {
                                "task_id": "two",
                                "repetition": 1,
                                "run_id": "run-2",
                                "base_id": "base-2",
                                "status": "visible_failure",
                                "process_exit_code": 1,
                                "timed_out": False,
                                "trace": {},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = audit_heldout_base_execution(
                execution_path=execution,
                runs_root=runs,
                base_root=bases,
            )
            self.assertEqual(report["audited_counts"]["eligible_public"], 1)
            self.assertEqual(report["audited_counts"]["infrastructure_failure"], 1)
            self.assertEqual(report["audited_counts"]["visible_failure"], 0)
            self.assertEqual(
                report["slots"][1]["process_error_category"],
                "model_credits_exhausted",
            )


if __name__ == "__main__":
    unittest.main()

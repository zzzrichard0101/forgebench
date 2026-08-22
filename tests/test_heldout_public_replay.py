import json
import tempfile
import unittest
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.completion import protected_paths
from forgebench.heldout_public_replay import HeldoutPublicReplayRunner
from forgebench.workspace import create_isolated_workspace, initialize_git_workspace


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "python-plugin-boundary" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-plugin-boundary"


class HeldoutPublicReplayTests(unittest.TestCase):
    def _base(self, root: Path):
        source = create_isolated_workspace(SEED, root / "sources", "source")
        initialize_git_workspace(source)
        (source / ".forgebench").mkdir()
        (source / ".forgebench" / "plan.json").write_text(
            json.dumps(
                {
                    "objective": "Complete the public task.",
                    "steps": [{"action": "Inspect", "verification": "Check"}],
                    "completion_checks": ["artifact exists"],
                    "immutable_paths": list(protected_paths(TASK)),
                }
            ),
            encoding="utf-8",
        )
        return BaseCompletionStore(root / "bases").seal(
            task=TASK,
            seed=SEED,
            source_workspace=source,
            source_run_id="source",
            base_id="base-1",
        )

    def test_accept_all_defers_hidden_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = self._base(root)
            result = HeldoutPublicReplayRunner(root / "runs").run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="accept_all",
                assignment={"probe_selected": False, "model_selected": False},
                assignment_manifest_id="assignment",
                assignment_manifest_sha256="sha256:assignment",
                run_id="accept",
            )
            record = json.loads(
                (result.workspace.parent / "public-policy-replay.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIsNone(record["evaluation"]["hidden_task_passed_after"])
            self.assertTrue(record["evaluation"]["hidden_evaluation_deferred"])
            self.assertFalse(record["private_grader_invoked"])
            self.assertFalse(record["routing"]["model_attempted"])

    def test_probe_all_records_probe_without_hidden_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = self._base(root)
            result = HeldoutPublicReplayRunner(root / "runs").run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="probe_all",
                assignment={"probe_selected": True, "model_selected": False},
                assignment_manifest_id="assignment",
                assignment_manifest_sha256="sha256:assignment",
                run_id="probe",
            )
            self.assertIsNotNone(result.deterministic_probe)
            self.assertTrue(
                (result.workspace.parent / "deterministic-probe.json").is_file()
            )

    def test_model_selected_assignment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = self._base(root)
            with self.assertRaisesRegex(ValueError, "cannot execute a model-selected"):
                HeldoutPublicReplayRunner(root / "runs").run(
                    task=TASK,
                    seed=SEED,
                    base=base,
                    policy="accept_all",
                    assignment={"probe_selected": False, "model_selected": True},
                    assignment_manifest_id="assignment",
                    assignment_manifest_sha256="sha256:assignment",
                    run_id="rejected",
                )


if __name__ == "__main__":
    unittest.main()

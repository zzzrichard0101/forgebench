import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.completion import protected_paths
from forgebench.heldout_model_replay import HeldoutModelReplayRunner
from forgebench.workspace import create_isolated_workspace, initialize_git_workspace


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "python-plugin-boundary" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-plugin-boundary"


class HeldoutModelReplayTests(unittest.TestCase):
    def _base(self, root: Path):
        source = create_isolated_workspace(SEED, root / "sources", "source")
        initialize_git_workspace(source)
        plan = source / ".forgebench" / "plan.json"
        plan.parent.mkdir()
        plan.write_text(
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
        implementation = source / "plugin_loader.py"
        text = implementation.read_text(encoding="utf-8")
        text = text.replace(
            'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n    return entrypoint.read_text(encoding="utf-8")',
            'root = plugin_root.resolve()\n    entrypoint = (root / manifest["entrypoint"]).resolve()\n    if not entrypoint.is_relative_to(root):\n        raise ValueError("outside plugin root")\n    return entrypoint.read_text(encoding="utf-8")',
        )
        implementation.write_text(text, encoding="utf-8")
        return BaseCompletionStore(root / "bases").seal(
            task=TASK,
            seed=SEED,
            source_workspace=source,
            source_run_id="source",
            base_id="base-1",
        )

    @staticmethod
    def _command(prompt: str, workspace: Path) -> list[str]:
        script = (
            "import json; print(json.dumps({'type':'turn.completed','usage':"
            "{'input_tokens':20,'cached_input_tokens':10,'output_tokens':3}}))"
        )
        return [sys.executable, "-c", script]

    def test_verify_all_calls_model_and_defers_hidden_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = HeldoutModelReplayRunner(root / "runs").run(
                task=TASK,
                seed=SEED,
                base=self._base(root),
                policy="verify_all",
                assignment={"probe_selected": False, "model_selected": True},
                assignment_manifest_id="assignment",
                assignment_manifest_sha256="sha256:assignment",
                command_factory=self._command,
                timeout_seconds=30,
                run_id="verify",
            )
            record = json.loads(
                (result.workspace.parent / "model-policy-replay.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(result.model_attempted)
            self.assertEqual(result.input_tokens, 20)
            self.assertIsNone(record["evaluation"]["hidden_task_passed_after"])
            self.assertTrue(record["evaluation"]["hidden_evaluation_deferred"])
            self.assertFalse(record["private_grader_invoked"])

    def test_unselected_random_k_makes_no_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def forbidden(prompt: str, workspace: Path) -> list[str]:
                self.fail("unselected Random-k must not construct a model command")

            result = HeldoutModelReplayRunner(root / "runs").run(
                task=TASK,
                seed=SEED,
                base=self._base(root),
                policy="random_k_call_matched",
                assignment={"probe_selected": False, "model_selected": False},
                assignment_manifest_id="assignment",
                assignment_manifest_sha256="sha256:assignment",
                command_factory=forbidden,
                timeout_seconds=30,
                run_id="random-skip",
            )
            self.assertFalse(result.model_attempted)
            self.assertEqual(result.input_tokens, 0)

    def test_hierarchical_route_records_probe_before_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompts: list[str] = []

            def command(prompt: str, workspace: Path) -> list[str]:
                prompts.append(prompt)
                return self._command(prompt, workspace)

            result = HeldoutModelReplayRunner(root / "runs").run(
                task=TASK,
                seed=SEED,
                base=self._base(root),
                policy="risk_hierarchical",
                assignment={"probe_selected": True, "model_selected": True},
                assignment_manifest_id="assignment",
                assignment_manifest_sha256="sha256:assignment",
                command_factory=command,
                timeout_seconds=30,
                run_id="hierarchical",
            )
            self.assertIsNotNone(result.probe)
            self.assertTrue(result.model_attempted)
            self.assertIn("DETERMINISTIC_PROBE_JSON", prompts[0])


if __name__ == "__main__":
    unittest.main()

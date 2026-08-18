import json
import copy
import tempfile
import unittest
from pathlib import Path

from forgebench.completion import CompletionVerifier
from forgebench.completion_risk import CompletionRiskPolicy
from forgebench.deterministic_probe import DeterministicProbeRunner
from forgebench.workspace import create_isolated_workspace, initialize_git_workspace


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "python-plugin-boundary" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-plugin-boundary"


class DeterministicProbeTests(unittest.TestCase):
    def test_file_type_probe_exposes_non_python_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_isolated_workspace(SEED, Path(temp), "probe")
            initialize_git_workspace(workspace)
            plan = {
                "objective": "Keep entrypoints inside the plugin root.",
                "steps": [
                    {"action": "Resolve path", "verification": "Run tests"},
                    {"action": "Inspect diff", "verification": "Check API"},
                ],
                "completion_checks": ["public tests pass"],
                "immutable_paths": ["SECURITY.md", "secret.txt", "requirements.txt"],
            }
            plan_path = workspace / ".forgebench" / "plan.json"
            plan_path.parent.mkdir()
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            implementation = workspace / "plugin_loader.py"
            text = implementation.read_text(encoding="utf-8")
            text = text.replace(
                'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n    return entrypoint.read_text(encoding="utf-8")',
                'root = plugin_root.resolve()\n    entrypoint = (root / manifest["entrypoint"]).resolve()\n    if not entrypoint.is_relative_to(root):\n        raise ValueError("outside plugin root")\n    return entrypoint.read_text(encoding="utf-8")',
            )
            implementation.write_text(text, encoding="utf-8")
            completion = CompletionVerifier().verify(TASK, workspace, SEED)
            decision = CompletionRiskPolicy().evaluate(
                task=TASK, workspace=workspace, completion=completion
            )

            result = DeterministicProbeRunner().run(
                task=TASK, workspace=workspace, decision=decision
            )

            self.assertTrue(result.supported)
            self.assertFalse(result.passed)
            outcomes = {case.probe_id: case.outcome for case in result.cases}
            self.assertEqual(outcomes["plugin_directory_entrypoint"], "passed")
            self.assertEqual(outcomes["plugin_non_python_regular_file"], "failed")

    def test_probe_selection_depends_on_interface_contract_not_task_id(self) -> None:
        renamed = copy.deepcopy(TASK)
        renamed["id"] = "unseen-heldout-analogue"
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_isolated_workspace(SEED, Path(temp), "renamed")
            initialize_git_workspace(workspace)
            implementation = workspace / "plugin_loader.py"
            text = implementation.read_text(encoding="utf-8").replace(
                'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n    return entrypoint.read_text(encoding="utf-8")',
                'root = plugin_root.resolve()\n    entrypoint = (root / manifest["entrypoint"]).resolve()\n    if not entrypoint.is_relative_to(root):\n        raise ValueError("outside plugin root")\n    return entrypoint.read_text(encoding="utf-8")',
            )
            implementation.write_text(text, encoding="utf-8")
            plan_path = workspace / ".forgebench" / "plan.json"
            plan_path.parent.mkdir()
            plan_path.write_text("{}", encoding="utf-8")
            completion = CompletionVerifier().verify(renamed, workspace, SEED)
            decision = CompletionRiskPolicy().evaluate(
                task=renamed, workspace=workspace, completion=completion
            )

            result = DeterministicProbeRunner().run(
                task=renamed, workspace=workspace, decision=decision
            )

            self.assertTrue(result.supported)
            self.assertEqual(result.adapter_id, "python-manifest-file-loader-v1")
            self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.base_completion import (
    BaseCompletionStore,
    HiddenLabelStore,
    PolicyReplayRunner,
)
from forgebench.grader import DeterministicGrader
from forgebench.workspace import (
    WorkspaceError,
    create_isolated_workspace,
    hash_workspace,
    initialize_git_workspace,
)


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "python-plugin-boundary" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-plugin-boundary"
GRADERS = ROOT / "benchmark" / "graders"


class BaseCompletionTests(unittest.TestCase):
    def _source(self, root: Path, *, fully_fixed: bool = False) -> Path:
        source = create_isolated_workspace(SEED, root / "sources", "source")
        initialize_git_workspace(source)
        plan = {
            "objective": "Keep plugin entrypoints inside the plugin root.",
            "steps": [
                {"action": "Resolve path", "verification": "Run tests"},
                {"action": "Inspect diff", "verification": "Check API"},
            ],
            "completion_checks": ["public tests pass"],
            "immutable_paths": ["SECURITY.md", "secret.txt", "requirements.txt"],
        }
        plan_path = source / ".forgebench" / "plan.json"
        plan_path.parent.mkdir()
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        implementation = source / "plugin_loader.py"
        text = implementation.read_text(encoding="utf-8")
        condition = "if not entrypoint.is_relative_to(root):"
        replacement = condition
        if fully_fixed:
            replacement = (
                'if not entrypoint.is_relative_to(root) or '
                'entrypoint.suffix != ".py" or not entrypoint.is_file():'
            )
        text = text.replace(
            'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n'
            '    return entrypoint.read_text(encoding="utf-8")',
            'root = plugin_root.resolve()\n'
            '    entrypoint = (root / manifest["entrypoint"]).resolve()\n'
            f"    {replacement}\n"
            '        raise ValueError("outside plugin root")\n'
            '    return entrypoint.read_text(encoding="utf-8")',
        )
        implementation.write_text(text, encoding="utf-8")
        return source

    def test_seal_contains_public_evidence_and_hidden_label_is_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source(root)
            store = BaseCompletionStore(root / "base-completions")
            base = store.seal(
                task=TASK,
                seed=SEED,
                source_workspace=source,
                source_run_id="source-run",
                base_id="base-1",
            )
            public_text = (base.root / "public-base-record.json").read_text(
                encoding="utf-8"
            )
            self.assertTrue(base.eligible)
            self.assertNotIn("hidden", public_text.lower())
            self.assertEqual(store.load("base-1").workspace_hash, base.workspace_hash)

            labels = root / "labels"
            grade = HiddenLabelStore(
                labels, DeterministicGrader(GRADERS)
            ).evaluate(base=base, task=TASK, seed=SEED)
            self.assertFalse(grade.passed)
            self.assertTrue((labels / "base-1.json").is_file())
            self.assertFalse((base.root / "hidden-label.json").exists())

    def test_tampered_sealed_workspace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = BaseCompletionStore(root / "base-completions").seal(
                task=TASK,
                seed=SEED,
                source_workspace=self._source(root),
                source_run_id="source-run",
                base_id="base-1",
            )
            (base.workspace / "plugin_loader.py").write_text("tampered", encoding="utf-8")
            with self.assertRaises(WorkspaceError):
                BaseCompletionStore(root / "base-completions").load("base-1")

    def test_base_identifier_cannot_escape_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                BaseCompletionStore(root / "base-completions").seal(
                    task=TASK,
                    seed=SEED,
                    source_workspace=self._source(root),
                    source_run_id="source-run",
                    base_id="../outside",
                )

    def test_accept_and_probe_all_reuse_one_immutable_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._source(root)
            base = BaseCompletionStore(root / "base-completions").seal(
                task=TASK,
                seed=SEED,
                source_workspace=source,
                source_run_id="source-run",
                base_id="base-1",
            )
            before = hash_workspace(base.workspace)
            runner = PolicyReplayRunner(
                root / "policy-runs", DeterministicGrader(GRADERS)
            )

            accepted = runner.run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="accept_all",
                run_id="accept-run",
            )
            probed = runner.run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="probe_all",
                run_id="probe-run",
            )

            self.assertEqual(accepted.base_workspace_hash, probed.base_workspace_hash)
            self.assertEqual(hash_workspace(base.workspace), before)
            self.assertFalse(accepted.model_attempted)
            self.assertIsNotNone(probed.deterministic_probe)
            self.assertFalse(probed.deterministic_probe.passed)
            self.assertFalse(accepted.grade_after.passed)
            self.assertFalse(probed.grade_after.passed)

    def test_hierarchical_policy_repairs_a_copy_after_probe_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = BaseCompletionStore(root / "base-completions").seal(
                task=TASK,
                seed=SEED,
                source_workspace=self._source(root),
                source_run_id="source-run",
                base_id="base-1",
            )
            base_before = hash_workspace(base.workspace)

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                self.assertIn("plugin_non_python_regular_file", prompt)
                script = (
                    "import json; from pathlib import Path; "
                    "p=Path('plugin_loader.py'); s=p.read_text(encoding='utf-8'); "
                    "s=s.replace('if not entrypoint.is_relative_to(root):', "
                    "'if not entrypoint.is_relative_to(root) or entrypoint.suffix != \".py\" or not entrypoint.is_file():'); "
                    "p.write_text(s, encoding='utf-8'); "
                    "print(json.dumps({'type':'turn.completed','usage':"
                    "{'input_tokens':10,'cached_input_tokens':4,'output_tokens':3}}))"
                )
                return [sys.executable, "-c", script]

            result = PolicyReplayRunner(
                root / "policy-runs", DeterministicGrader(GRADERS)
            ).run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="risk_hierarchical",
                command_factory=command_factory,
                run_id="hierarchical-run",
            )

            self.assertTrue(result.model_attempted)
            self.assertTrue(result.grade_after.passed)
            self.assertEqual(result.input_tokens, 10)
            self.assertEqual(hash_workspace(base.workspace), base_before)
            self.assertNotEqual(
                hash_workspace(result.workspace), hash_workspace(base.workspace)
            )

    def test_random_k_requires_an_explicit_frozen_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = BaseCompletionStore(root / "base-completions").seal(
                task=TASK,
                seed=SEED,
                source_workspace=self._source(root, fully_fixed=True),
                source_run_id="source-run",
                base_id="base-1",
            )
            runner = PolicyReplayRunner(
                root / "policy-runs", DeterministicGrader(GRADERS)
            )
            with self.assertRaises(ValueError):
                runner.run(
                    task=TASK,
                    seed=SEED,
                    base=base,
                    policy="random_k_call_matched",
                )

            result = runner.run(
                task=TASK,
                seed=SEED,
                base=base,
                policy="random_k_call_matched",
                random_selected=False,
                run_id="random-skip",
            )
            self.assertFalse(result.selected)
            self.assertFalse(result.model_attempted)
            self.assertTrue(result.grade_after.passed)


if __name__ == "__main__":
    unittest.main()

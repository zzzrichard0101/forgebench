import json
import tempfile
import unittest
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.comparison_manifest import (
    ComparisonCandidate,
    ComparisonManifestPlanner,
    load_comparison_manifest,
    validate_assignment,
)
from forgebench.workspace import (
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


class ComparisonManifestTests(unittest.TestCase):
    def _source(self, root: Path, run_id: str, *, fully_fixed: bool) -> Path:
        source = create_isolated_workspace(SEED, root / "sources", run_id)
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
        if fully_fixed:
            condition = (
                'if not entrypoint.is_relative_to(root) or '
                'entrypoint.suffix != ".py" or not entrypoint.is_file():'
            )
        text = text.replace(
            'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n'
            '    return entrypoint.read_text(encoding="utf-8")',
            'root = plugin_root.resolve()\n'
            '    entrypoint = (root / manifest["entrypoint"]).resolve()\n'
            f"    {condition}\n"
            '        raise ValueError("outside plugin root")\n'
            '    return entrypoint.read_text(encoding="utf-8")',
        )
        implementation.write_text(text, encoding="utf-8")
        return source

    def _bases(self, root: Path):
        store = BaseCompletionStore(root / "base-completions")
        false_base = store.seal(
            task=TASK,
            seed=SEED,
            source_workspace=self._source(root, "false-source", fully_fixed=False),
            source_run_id="false-source-run",
            base_id="false-base",
        )
        true_base = store.seal(
            task=TASK,
            seed=SEED,
            source_workspace=self._source(root, "true-source", fully_fixed=True),
            source_run_id="true-source-run",
            base_id="true-base",
        )
        return false_base, true_base

    def test_planner_matches_random_k_calls_without_hidden_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            false_base, true_base = self._bases(root)
            hashes_before = {
                false_base.base_id: hash_workspace(false_base.workspace),
                true_base.base_id: hash_workspace(true_base.workspace),
            }
            path = root / "manifests" / "comparison-v1.json"
            manifest = ComparisonManifestPlanner(root / "routing").plan(
                candidates=[
                    ComparisonCandidate(false_base, TASK),
                    ComparisonCandidate(true_base, TASK),
                ],
                output_path=path,
                random_seed=1729,
                manifest_id="comparison-v1",
            )

            false_assignment = manifest.assignment("false-base")
            true_assignment = manifest.assignment("true-base")
            self.assertTrue(
                false_assignment["policies"]["risk_hierarchical"]["model_selected"]
            )
            self.assertFalse(
                true_assignment["policies"]["risk_hierarchical"]["model_selected"]
            )
            random_calls = sum(
                item["policies"]["random_k_call_matched"]["model_selected"]
                for item in manifest.payload["bases"]
            )
            hierarchical_calls = sum(
                item["policies"]["risk_hierarchical"]["model_selected"]
                for item in manifest.payload["bases"]
            )
            self.assertEqual(random_calls, hierarchical_calls)
            self.assertEqual(random_calls, 1)
            serialized = json.dumps(manifest.payload).lower()
            self.assertNotIn("hidden_task_passed", serialized)
            self.assertNotIn("grader-result", serialized)
            self.assertEqual(hash_workspace(false_base.workspace), hashes_before["false-base"])
            self.assertEqual(hash_workspace(true_base.workspace), hashes_before["true-base"])

    def test_manifest_hash_and_assignment_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            false_base, _ = self._bases(root)
            path = root / "manifests" / "comparison-v1.json"
            ComparisonManifestPlanner(root / "routing").plan(
                candidates=[ComparisonCandidate(false_base, TASK)],
                output_path=path,
                random_seed=7,
                manifest_id="comparison-v1",
            )
            loaded = load_comparison_manifest(path)
            assignment = validate_assignment(
                manifest=loaded,
                base=false_base,
                task=TASK,
                policy="random_k_call_matched",
            )
            self.assertTrue(assignment["model_selected"])

            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["random_seed"] = 8
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_comparison_manifest(path)

    def test_same_seed_produces_same_random_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            false_base, true_base = self._bases(root)
            candidates = [
                ComparisonCandidate(false_base, TASK),
                ComparisonCandidate(true_base, TASK),
            ]
            first = ComparisonManifestPlanner(root / "routing-a").plan(
                candidates=candidates,
                output_path=root / "first.json",
                random_seed=99,
                manifest_id="first",
            )
            second = ComparisonManifestPlanner(root / "routing-b").plan(
                candidates=candidates,
                output_path=root / "second.json",
                random_seed=99,
                manifest_id="second",
            )
            first_random = {
                item["base_id"]: item["policies"]["random_k_call_matched"]
                for item in first.payload["bases"]
            }
            second_random = {
                item["base_id"]: item["policies"]["random_k_call_matched"]
                for item in second.payload["bases"]
            }
            self.assertEqual(first_random, second_random)


if __name__ == "__main__":
    unittest.main()

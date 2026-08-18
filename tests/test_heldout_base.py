import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.heldout_base import HeldoutBaseRunner, build_base_matrix


class HeldoutBaseRunnerTests(unittest.TestCase):
    def _task(self, seed: Path) -> dict:
        return {
            "id": "heldout-public-only",
            "version": 1,
            "family": "development",
            "budgets": {"max_seconds": 30},
            "public_checks": [],
            "grader": {
                "checks": [
                    {
                        "id": "protected",
                        "type": "workspace_policy",
                        "severity": "required",
                        "protected_paths": ["POLICY.md"],
                    },
                    {
                        "id": "private",
                        "type": "command",
                        "severity": "required",
                        "argv": ["{python}", "{grader_root}/grade.py"],
                    },
                ]
            },
            "evidence": {
                "required_artifacts": [
                    "workspace.diff",
                    "trace.jsonl",
                    "grader-result.json",
                ]
            },
            "instruction": "Preserve the public fixture.",
        }

    def _command_factory(self, *, exit_code: int = 0):
        plan = {
            "objective": "Preserve the fixture",
            "steps": [{"action": "inspect", "verification": "policy unchanged"}],
            "completion_checks": ["policy unchanged"],
            "immutable_paths": ["POLICY.md"],
        }
        script = (
            "from pathlib import Path; import json; "
            "Path('.forgebench').mkdir(); "
            f"Path('.forgebench/plan.json').write_text({json.dumps(json.dumps(plan))}); "
            "print(json.dumps({'type':'turn.completed','usage':"
            "{'input_tokens':10,'cached_input_tokens':4,'output_tokens':3}})); "
            f"raise SystemExit({exit_code})"
        )

        def factory(_prompt: str, _workspace: Path) -> list[str]:
            return [sys.executable, "-c", script]

        return factory

    def test_public_completion_is_sealed_without_private_grader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            seed = root / "seed"
            seed.mkdir()
            (seed / "POLICY.md").write_text("immutable\n", encoding="utf-8")
            result = HeldoutBaseRunner(root / "runs", root / "bases").run(
                task=self._task(seed),
                seed=seed,
                repetition=1,
                base_id="heldout-base-r1",
                command_factory=self._command_factory(),
            )
            self.assertTrue(result.public_completion_eligible)
            self.assertIsNotNone(result.base)
            record = json.loads(
                (result.workspace.parent / "heldout-base-run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(record["hidden_grader_invoked"])
            self.assertNotIn("grader_root", json.dumps(record))

    def test_nonzero_process_is_retained_but_not_sealed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            seed = root / "seed"
            seed.mkdir()
            (seed / "POLICY.md").write_text("immutable\n", encoding="utf-8")
            result = HeldoutBaseRunner(root / "runs", root / "bases").run(
                task=self._task(seed),
                seed=seed,
                repetition=1,
                base_id="heldout-base-r1",
                command_factory=self._command_factory(exit_code=1),
            )
            self.assertFalse(result.public_completion_eligible)
            self.assertIsNone(result.base)

    def test_matrix_has_three_slots_per_task(self) -> None:
        tasks = [
            {"id": "one", "version": 1, "family": "development"},
            {"id": "two", "version": 2, "family": "incident"},
        ]
        matrix = build_base_matrix(tasks, repetitions=3, snapshot="heldout-v1")
        self.assertEqual(len(matrix), 6)
        self.assertEqual(matrix[0]["base_id"], "heldout-v1--one--r1")
        self.assertEqual(matrix[-1]["base_id"], "heldout-v1--two--r3")


if __name__ == "__main__":
    unittest.main()

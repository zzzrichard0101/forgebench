import json
import shutil
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from forgebench.grader import DeterministicGrader

from scripts.hash_seed import hash_seed
from scripts.validate_task import validate_task


ROOT = Path(__file__).resolve().parents[1]
GRADERS = ROOT / "benchmark" / "graders"


def load_catalog() -> list[tuple[dict, Path]]:
    task_paths = sorted((ROOT / "benchmark" / "examples").glob("**/task.json"))
    task_paths += sorted((ROOT / "benchmark" / "tasks").glob("**/task.json"))
    return [
        (json.loads(path.read_text(encoding="utf-8")), path)
        for path in task_paths
    ]


class BenchmarkCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog()
        self.grader = DeterministicGrader(GRADERS)

    def test_all_task_documents_validate(self) -> None:
        self.assertGreaterEqual(len(self.catalog), 4)
        for task, path in self.catalog:
            with self.subTest(path=path):
                self.assertEqual(validate_task(task), [])
                seed = ROOT / task["seed_repo"]["source"]
                self.assertTrue(seed.is_dir())
                if task["split"] == "dev":
                    self.assertEqual(task["seed_repo"]["revision"], hash_seed(seed))

    def test_catalog_covers_all_task_families(self) -> None:
        self.assertEqual(
            {task["family"] for task, _ in self.catalog},
            {"development", "incident", "adversarial"},
        )

    def test_every_seed_is_known_bad_and_deterministic(self) -> None:
        for task, _ in self.catalog:
            seed = ROOT / task["seed_repo"]["source"]
            with self.subTest(task=task["id"]):
                results = [self.grader.grade(task, seed, seed) for _ in range(3)]
                self.assertFalse(results[0].passed)
                self.assertEqual(
                    [asdict(result) for result in results],
                    [asdict(results[0])] * 3,
                )

    def test_new_tasks_have_known_good_solution(self) -> None:
        solutions = {
            "python-config-precedence": self._fix_config,
            "checkout-retry-incident": self._fix_incident,
            "python-plugin-boundary": self._fix_plugin,
        }
        for task, _ in self.catalog:
            if task["id"] not in solutions:
                continue
            seed = ROOT / task["seed_repo"]["source"]
            with self.subTest(task=task["id"]), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / "workspace"
                shutil.copytree(seed, workspace)
                solutions[task["id"]](workspace)
                result = self.grader.grade(task, workspace, seed)
                self.assertTrue(result.passed, result)

    def test_protected_file_mutation_is_detected_for_every_task(self) -> None:
        for task, _ in self.catalog:
            policies = [
                check
                for check in task["grader"]["checks"]
                if check["type"] == "workspace_policy"
            ]
            self.assertTrue(policies, task["id"])
            seed = ROOT / task["seed_repo"]["source"]
            with self.subTest(task=task["id"]), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / "workspace"
                shutil.copytree(seed, workspace)
                protected = workspace / policies[0]["protected_paths"][0]
                protected.write_text("mutation\n", encoding="utf-8")
                result = self.grader.grade(task, workspace, seed)
                policy_results = [
                    check for check in result.checks if check.check_type == "workspace_policy"
                ]
                self.assertTrue(any(not check.passed for check in policy_results))

    @staticmethod
    def _fix_config(workspace: Path) -> None:
        path = workspace / "config_loader.py"
        source = path.read_text(encoding="utf-8")
        source = source.replace("if env_value:", "if env_value is not None:")
        source = source.replace(
            'if file_config.get("timeout"):', 'if "timeout" in file_config:'
        )
        path.write_text(source, encoding="utf-8")

    @staticmethod
    def _fix_incident(workspace: Path) -> None:
        report = {
            "incident_id": "checkout-retry-storm-2026-08-15",
            "root_cause": "retry_on_non_transient_400",
            "impact": {"affected_requests": 3, "total_retry_attempts": 9},
            "evidence": [
                "Three requests returned HTTP 400 across four attempts each.",
                "The retry policy incorrectly marks status 400 as retryable.",
            ],
            "remediation": {
                "config_change": "Remove HTTP 400 from retryable_statuses.",
                "verification": "Add a regression check that 400 responses stop after one attempt.",
            },
        }
        (workspace / "incident_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _fix_plugin(workspace: Path) -> None:
        path = workspace / "plugin_loader.py"
        source = path.read_text(encoding="utf-8")
        old = 'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n    return entrypoint.read_text(encoding="utf-8")'
        new = '''root = plugin_root.resolve()
    declared = Path(manifest["entrypoint"])
    if declared.is_absolute():
        raise ValueError("absolute plugin entrypoint")
    entrypoint = (root / declared).resolve()
    if not entrypoint.is_relative_to(root) or entrypoint.suffix != ".py":
        raise ValueError("plugin entrypoint escapes trust boundary")
    return entrypoint.read_text(encoding="utf-8")'''
        if old not in source:
            raise AssertionError("fixture source changed")
        path.write_text(source.replace(old, new), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

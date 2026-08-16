import json
import shutil
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog, CatalogError, hash_seed
from forgebench.grader import DeterministicGrader
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

    def test_manifest_catalog_resolves_every_task(self) -> None:
        catalog = BenchmarkCatalog(ROOT, ROOT / "benchmark" / "manifest.json")
        self.assertEqual(len(catalog.list()), len(self.catalog))
        for task, _ in self.catalog:
            self.assertEqual(catalog.get(task["id"]).task, task)

    def test_unknown_catalog_task_is_explicit(self) -> None:
        catalog = BenchmarkCatalog(ROOT, ROOT / "benchmark" / "manifest.json")
        with self.assertRaises(CatalogError):
            catalog.get("missing-task")

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
            "python-pagination-cursor": self._fix_pagination,
            "python-event-deduplication": self._fix_deduplication,
            "python-rate-window": self._fix_rate_window,
            "worker-visibility-incident": self._fix_worker_incident,
            "cdn-cache-incident": self._fix_cdn_incident,
            "python-archive-boundary": self._fix_archive,
        }
        self.assertEqual(
            set(solutions),
            {task["id"] for task, _ in self.catalog if task["split"] == "dev"},
        )
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
            "incident_id": "checkout-400-retries",
            "root_cause": "HTTP 400 was incorrectly marked retryable",
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

    @staticmethod
    def _replace(workspace: Path, filename: str, old: str, new: str) -> None:
        path = workspace / filename
        source = path.read_text(encoding="utf-8")
        if old not in source:
            raise AssertionError(f"fixture source changed: {filename}")
        path.write_text(source.replace(old, new), encoding="utf-8")

    @classmethod
    def _fix_pagination(cls, workspace: Path) -> None:
        cls._replace(
            workspace,
            "pagination.py",
            "start = max((cursor or 0) - (1 if cursor else 0), 0)",
            "start = cursor or 0",
        )

    @classmethod
    def _fix_deduplication(cls, workspace: Path) -> None:
        cls._replace(
            workspace,
            "dedup.py",
            'key = event["user_id"]',
            'key = event["event_id"]',
        )

    @classmethod
    def _fix_rate_window(cls, workspace: Path) -> None:
        cls._replace(workspace, "rate_limit.py", "timestamp >= cutoff", "timestamp > cutoff")

    @staticmethod
    def _fix_worker_incident(workspace: Path) -> None:
        report = {
            "incident_id": "duplicate-worker-deliveries",
            "root_cause": "Visibility timeout is shorter than job runtime",
            "impact": {"duplicated_jobs": 2, "extra_attempts": 2},
            "evidence": [
                "Visibility timeout is 30 seconds.",
                "Jobs 1 and 3 run for 38 to 42 seconds and receive second attempts.",
            ],
            "remediation": {
                "config_change": "Raise the visibility timeout above maximum job runtime.",
                "verification": "Run long jobs and assert each job ID has exactly one completion.",
            },
        }
        (workspace / "incident_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _fix_cdn_incident(workspace: Path) -> None:
        report = {
            "incident_id": "stale-web-deployment",
            "root_cause": "Cache TTL increased from one minute to one hour",
            "impact": {
                "stale_responses": 499,
                "affected_regions": ["ap-northeast-2", "us-west-2"],
            },
            "evidence": [
                "Deployment raised cache TTL from 60 to 3600 seconds.",
                "Stale responses began after deployment in two regions.",
            ],
            "remediation": {
                "config_change": "Rollback cache TTL to 60 seconds and purge affected caches.",
                "verification": "Compare stale-response metrics in every region after cache purge.",
            },
        }
        (workspace / "incident_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )

    @classmethod
    def _fix_archive(cls, workspace: Path) -> None:
        old = "return (root / member_name).resolve()"
        new = '''resolved_root = root.resolve()
    member = Path(member_name)
    if member.is_absolute():
        raise ValueError("absolute archive member")
    target = (resolved_root / member).resolve()
    if not target.is_relative_to(resolved_root):
        raise ValueError("archive member escapes extraction root")
    return target'''
        cls._replace(workspace, "archive.py", old, new)


if __name__ == "__main__":
    unittest.main()

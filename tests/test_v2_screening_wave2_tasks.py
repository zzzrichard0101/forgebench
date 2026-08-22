import json
import subprocess
import sys
import unittest
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog, hash_seed


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmark" / "v2-development-wave2" / "manifest.json"
REPORT = ROOT / "experiments" / "reports" / "v2-screening-wave2-task-authoring-v1.json"


class V2ScreeningWave2TaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = BenchmarkCatalog(ROOT, MANIFEST)

    def test_catalog_contains_six_new_lineages(self) -> None:
        bundles = self.catalog.list()
        self.assertEqual(len(bundles), 6)
        self.assertEqual(len({bundle.task["id"] for bundle in bundles}), 6)
        self.assertEqual(len({bundle.task["seed_repo"]["revision"] for bundle in bundles}), 6)
        self.assertTrue(all(bundle.task["id"].startswith("v2-") for bundle in bundles))

    def test_seed_hashes_are_content_addressed(self) -> None:
        for bundle in self.catalog.list():
            self.assertEqual(bundle.task["seed_repo"]["revision"], hash_seed(bundle.seed_path))

    def test_public_checks_pass_while_private_source_is_absent(self) -> None:
        for bundle in self.catalog.list():
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                cwd=bundle.seed_path,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, bundle.task["id"])
            hidden = ROOT / "benchmark" / "v2-development-wave2" / "graders" / bundle.task["id"]
            self.assertFalse(hidden.exists())

    def test_ids_and_seed_revisions_do_not_overlap_prior_catalogs(self) -> None:
        prior_ids = set()
        prior_revisions = set()
        for relative in (
            "benchmark/manifest.json",
            "heldout-public/manifest.json",
            "benchmark/v2-development/manifest.json",
        ):
            manifest = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            for record in manifest["tasks"]:
                prior_ids.add(record["id"])
                task = json.loads((ROOT / record["task_path"]).read_text(encoding="utf-8"))
                prior_revisions.add(task["seed_repo"]["revision"])
        for bundle in self.catalog.list():
            self.assertNotIn(bundle.task["id"], prior_ids)
            self.assertNotIn(bundle.task["seed_repo"]["revision"], prior_revisions)

    def test_public_report_contains_only_aggregate_private_evidence(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready_for_base_generation")
        self.assertEqual(report["task_count"], 6)
        self.assertEqual(report["public_catalog_sha256"], manifest["catalog_sha256"])
        self.assertEqual(report["grader_quality"]["seed_hidden_failures"], 18)
        self.assertEqual(report["grader_quality"]["known_good_hidden_successes"], 18)
        self.assertFalse(report["scope"]["model_base_completions_generated"])
        self.assertFalse(report["scope"]["independent_custodian"])
        rendered = json.dumps(report)
        self.assertNotIn("test_contract.py", rendered)
        self.assertNotIn("known-good", rendered)
        self.assertNotIn("C:\\\\Users", rendered)


if __name__ == "__main__":
    unittest.main()

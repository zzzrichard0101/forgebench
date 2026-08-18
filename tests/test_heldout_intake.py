import inspect
import json
import tempfile
import unittest
from pathlib import Path

from forgebench.catalog import hash_seed, hash_task_catalog
from forgebench.heldout_intake import (
    create_private_grader_seal,
    validate_heldout_intake,
)


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_MANIFEST = ROOT / "benchmark" / "manifest.json"
POLICY_FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "selective-verification-policy-freeze-v1.json"
)
REGISTERED_MANIFEST = ROOT / "heldout-public" / "manifest.json"
REGISTERED_SEAL = ROOT / "private-seal.json"
REGISTRATION_REPORT = (
    ROOT / "experiments" / "reports" / "heldout-intake-v1.json"
)


class HeldoutIntakeTests(unittest.TestCase):
    def _package(self, root: Path, *, probe_tasks: int = 3):
        records = []
        task_ids = []
        families = ["development"] * 4 + ["incident"] * 3 + ["adversarial"] * 3
        for index, family in enumerate(families):
            task_id = f"heldout-task-{index:02d}"
            task_ids.append(task_id)
            fixture = root / "heldout" / "fixtures" / task_id
            fixture.mkdir(parents=True)
            (fixture / "module.py").write_text(
                f"VALUE = {index}\n", encoding="utf-8"
            )
            task = {
                "id": task_id,
                "version": 1,
                "title": f"Independent held-out task {index}",
                "family": family,
                "difficulty": "medium",
                "split": "test",
                "seed_repo": {
                    "source": f"heldout/fixtures/{task_id}",
                    "revision": hash_seed(fixture),
                    "subdirectory": "",
                },
            }
            if index < probe_tasks:
                task["probe_contract"] = {
                    "version": 1,
                    "adapter": "python_manifest_file_loader",
                    "module": "module",
                    "callable": "load_file",
                    "manifest_key": "entrypoint",
                    "accepted_suffix": ".py",
                    "dimensions": ["file_type"],
                }
            task_path = root / "heldout" / "tasks" / task_id / "task.json"
            task_path.parent.mkdir(parents=True)
            task_path.write_text(json.dumps(task), encoding="utf-8")
            records.append(
                {
                    "id": task_id,
                    "version": 1,
                    "family": family,
                    "difficulty": "medium",
                    "split": "test",
                    "task_path": f"heldout/tasks/{task_id}/task.json",
                }
            )
        manifest = {
            "schema_version": 1,
            "snapshot": "heldout-v1",
            "frozen": True,
            "tasks": records,
        }
        manifest["catalog_sha256"] = hash_task_catalog(root, records)
        manifest_path = root / "heldout" / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        private_root = root / "private-graders"
        for task_id in task_ids:
            grader = private_root / task_id
            grader.mkdir(parents=True)
            (grader / "test_private.py").write_text(
                "PRIVATE_EXPECTATION = 'sealed-only'\n", encoding="utf-8"
            )
        seal_path = root / "seals" / "private.json"
        seal = create_private_grader_seal(
            private_root,
            task_ids,
            custodian_id="independent-reviewer",
            output_path=seal_path,
            attest_untouched_seed_fails=True,
            attest_known_good_outcome_passes=True,
            attest_protected_mutation_detected=True,
            attest_three_repeat_grade_deterministic=True,
        )
        return manifest_path, seal_path, private_root, seal

    def test_valid_independent_package_passes_without_grader_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, seal, _, _ = self._package(root)
            result = validate_heldout_intake(
                public_root=root,
                heldout_manifest_path=manifest,
                development_manifest_path=DEVELOPMENT_MANIFEST,
                private_seal_path=seal,
                policy_freeze_path=POLICY_FREEZE,
                policy_repository_root=ROOT,
            )
            self.assertEqual(result.task_count, 10)
            self.assertEqual(result.transferable_probe_tasks, 3)
            self.assertEqual(set(result.family_counts), {"development", "incident", "adversarial"})

    def test_registered_snapshot_matches_frozen_intake(self) -> None:
        result = validate_heldout_intake(
            public_root=ROOT,
            heldout_manifest_path=REGISTERED_MANIFEST,
            development_manifest_path=DEVELOPMENT_MANIFEST,
            private_seal_path=REGISTERED_SEAL,
            policy_freeze_path=POLICY_FREEZE,
            policy_repository_root=ROOT,
        )
        report = json.loads(REGISTRATION_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "accepted_not_executed")
        self.assertEqual(report["intake"], result.as_dict())
        self.assertEqual(report["execution_control"]["declared_attempts_used"], 0)
        self.assertEqual(report["execution_control"]["maximum_attempts"], 2)

    def test_public_intake_api_cannot_receive_private_grader_root(self) -> None:
        parameters = inspect.signature(validate_heldout_intake).parameters
        self.assertNotIn("grader_root", parameters)
        with tempfile.TemporaryDirectory() as temp:
            _, _, private_root, seal = self._package(Path(temp))
            serialized = json.dumps(seal)
            self.assertNotIn(str(private_root), serialized)
            self.assertNotIn("sealed-only", serialized)

    def test_too_few_transferable_probe_tasks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, seal, _, _ = self._package(root, probe_tasks=2)
            with self.assertRaisesRegex(ValueError, "at least 3 transferable"):
                validate_heldout_intake(
                    public_root=root,
                    heldout_manifest_path=manifest,
                    development_manifest_path=DEVELOPMENT_MANIFEST,
                    private_seal_path=seal,
                    policy_freeze_path=POLICY_FREEZE,
                    policy_repository_root=ROOT,
                )


if __name__ == "__main__":
    unittest.main()

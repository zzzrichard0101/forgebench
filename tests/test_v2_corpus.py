import json
import tempfile
import unittest
from pathlib import Path

from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import (
    MECHANISMS,
    audit_v2_labeled_corpus,
    payload_hash,
    validate_v2_public_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS = [
    ROOT / "benchmark" / "manifest.json",
    ROOT / "heldout-public" / "manifest.json",
]


class V2CorpusTests(unittest.TestCase):
    def _package(self, root: Path, *, false_count: int = 1, control_count: int = 1):
        cases = []
        labels = []
        mechanisms = sorted(MECHANISMS)
        cohorts = ["false_completion"] * false_count + ["passing_control"] * control_count
        for index, cohort in enumerate(cohorts):
            case_id = f"v2-case-{index:02d}"
            task_id = f"v2-task-{index:02d}"
            task_path = root / "tasks" / task_id / "task.json"
            base_path = root / "bases" / case_id / "base.json"
            evidence_path = root / "evidence" / case_id / "public.json"
            for path, payload in (
                (task_path, {"id": task_id, "version": 1}),
                (base_path, {"base_id": f"v2-base-{index:02d}"}),
                (evidence_path, {"completion_gate": "pass"}),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload), encoding="utf-8")
            cases.append(
                {
                    "case_id": case_id,
                    "task_id": task_id,
                    "task_version": 1,
                    "task_cluster_id": f"v2-cluster-{index:02d}",
                    "repository_lineage": f"v2-lineage-{index:02d}",
                    "seed_revision_sha256": "sha256:" + f"{index + 1:064x}",
                    "split": "mechanism_validation",
                    "task_path": task_path.relative_to(root).as_posix(),
                    "task_content_sha256": canonical_file_hash(task_path),
                    "base_id": f"v2-base-{index:02d}",
                    "base_artifact_path": base_path.relative_to(root).as_posix(),
                    "base_content_sha256": canonical_file_hash(base_path),
                    "public_evidence_path": evidence_path.relative_to(root).as_posix(),
                    "public_evidence_sha256": canonical_file_hash(evidence_path),
                    "public_completion_gate_passed": True,
                }
            )
            labels.append(
                {
                    "case_id": case_id,
                    "cohort": cohort,
                    "hidden_success_before": cohort == "passing_control",
                    "failure_mechanism": (
                        mechanisms[index % len(mechanisms)]
                        if cohort == "false_completion"
                        else None
                    ),
                    "hard_safety_violation_before": False,
                    "grader_version": "v2-grader-v1",
                    "grader_result_sha256": "sha256:" + f"{index + 1000:064x}",
                }
            )
        manifest = {
            "schema_version": 1,
            "corpus_version": "v2-development-corpus-v1",
            "snapshot": "v2-dev-test",
            "frozen": True,
            "cases": cases,
        }
        manifest["content_sha256"] = payload_hash(manifest)
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        oracle = {
            "schema_version": 1,
            "catalog_version": "v2-development-oracle-catalog-v1",
            "public_manifest_sha256": manifest["content_sha256"],
            "grader_seal_sha256": "sha256:" + "f" * 64,
            "labels": labels,
        }
        oracle["content_sha256"] = payload_hash(oracle)
        oracle_path = root / "private" / "oracle.json"
        oracle_path.parent.mkdir()
        oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
        return manifest, manifest_path, oracle, oracle_path

    def _validate(self, root: Path, manifest_path: Path):
        return validate_v2_public_corpus(
            public_root=root,
            manifest_path=manifest_path,
            repository_root=ROOT,
            exclusion_manifest_paths=EXCLUSIONS,
        )

    def test_public_and_oracle_catalogs_join_without_exposing_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, manifest_path, _, oracle_path = self._package(root)
            public = self._validate(root, manifest_path)
            audit = audit_v2_labeled_corpus(public, oracle_catalog_path=oracle_path)
            serialized_public = json.dumps(manifest)
            self.assertNotIn("hidden_success_before", serialized_public)
            self.assertNotIn("failure_mechanism", serialized_public)
            self.assertEqual(audit.false_completion_clusters, 1)
            self.assertEqual(audit.passing_control_clusters, 1)
            self.assertFalse(audit.validation_gate_population_ready)

    def test_public_base_id_accepts_sealed_store_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, manifest_path, _, _ = self._package(root)
            manifest["cases"][0]["base_id"] = "v2-screening--task--r1"
            manifest["content_sha256"] = payload_hash(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            public = self._validate(root, manifest_path)
            self.assertEqual(public.payload["cases"][0]["base_id"], "v2-screening--task--r1")

    def test_public_manifest_rejects_hidden_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, manifest_path, _, _ = self._package(root)
            manifest["cases"][0]["hidden_success_before"] = False
            manifest["content_sha256"] = payload_hash(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "public case fields"):
                self._validate(root, manifest_path)

    def test_v1_task_id_and_seed_revision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, manifest_path, _, _ = self._package(root)
            manifest["cases"][0]["task_id"] = "cache-key-collision-incident"
            manifest["content_sha256"] = payload_hash(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "overlaps excluded V1"):
                self._validate(root, manifest_path)

            manifest["cases"][0]["task_id"] = "v2-new-task"
            manifest["cases"][0]["seed_revision_sha256"] = (
                "sha256:b1b112f8499c9a39aaff3e359294c119f9db904ae1edbb8ed5d7005b9bb91943"
            )
            manifest["content_sha256"] = payload_hash(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "seed revision overlaps"):
                self._validate(root, manifest_path)

    def test_public_artifact_hash_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, manifest_path, _, _ = self._package(root)
            base = root / manifest["cases"][0]["base_artifact_path"]
            base.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                self._validate(root, manifest_path)

    def test_oracle_labels_must_be_complete_and_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, manifest_path, oracle, oracle_path = self._package(root)
            public = self._validate(root, manifest_path)
            oracle["labels"][0]["hidden_success_before"] = True
            oracle["content_sha256"] = payload_hash(oracle)
            oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "false-completion label"):
                audit_v2_labeled_corpus(public, oracle_catalog_path=oracle_path)

    def test_population_readiness_requires_preregistered_minimums(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, manifest_path, _, oracle_path = self._package(
                root, false_count=15, control_count=15
            )
            public = self._validate(root, manifest_path)
            audit = audit_v2_labeled_corpus(public, oracle_catalog_path=oracle_path)
            self.assertEqual(audit.false_completion_clusters, 15)
            self.assertEqual(audit.passing_control_clusters, 15)
            self.assertGreaterEqual(audit.failure_mechanisms, 6)
            self.assertTrue(audit.validation_gate_population_ready)


if __name__ == "__main__":
    unittest.main()


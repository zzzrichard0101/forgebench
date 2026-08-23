import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.v2_corpus import payload_hash


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_v2_screening_wave4_oracle.py"
GENERIC_SCRIPT = ROOT / "scripts" / "evaluate_v2_screening_oracle.py"


def _load(path: Path, name: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ScreeningWave4PrivateEvalRunnerTests(unittest.TestCase):
    def test_runner_targets_only_wave4_catalog_and_frozen_seal(self) -> None:
        runner = _load(SCRIPT, "evaluate_v2_screening_wave4_oracle")
        self.assertEqual(
            runner.TASK_MANIFEST,
            ROOT / "benchmark" / "v2-development-wave4" / "manifest.json",
        )
        self.assertEqual(len(runner.MECHANISMS), 10)
        self.assertEqual(
            runner.EXPECTED_GRADER_SEAL_SHA256,
            "sha256:1edb5b46d0f214535b0320848bed45f9dc795b150e8069916ec6f8fd33383b9a",
        )
        self.assertIn(
            ROOT / "benchmark" / "v2-development-wave3" / "manifest.json",
            runner.EXCLUSIONS,
        )

    def test_grader_content_is_verified_against_seal(self) -> None:
        evaluator = _load(GENERIC_SCRIPT, "evaluate_v2_screening_oracle_for_wave4_test")
        with tempfile.TemporaryDirectory() as temporary:
            grader_root = Path(temporary) / "graders"
            task_root = grader_root / "task-a"
            task_root.mkdir(parents=True)
            grader = task_root / "test_contract.py"
            grader.write_text("print('ok')\n", encoding="utf-8")

            import hashlib
            from forgebench.policy_freeze import canonical_file_hash

            digest = hashlib.sha256()
            relative = b"test_contract.py"
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(canonical_file_hash(grader).encode("ascii"))
            seal = {
                "schema_version": 1,
                "development_only": True,
                "task_graders": [
                    {
                        "task_id": "task-a",
                        "grader_sha256": "sha256:" + digest.hexdigest(),
                    }
                ],
            }
            seal["content_sha256"] = payload_hash(seal)
            evaluator.verify_grader_seal(grader_root, seal)
            grader.write_text("print('changed')\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluator.verify_grader_seal(grader_root, seal)

            tampered = json.loads(json.dumps(seal))
            tampered["development_only"] = False
            with self.assertRaises(ValueError):
                evaluator.verify_grader_seal(grader_root, tampered)


if __name__ == "__main__":
    unittest.main()

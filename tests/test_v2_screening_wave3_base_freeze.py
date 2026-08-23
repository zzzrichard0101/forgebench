import importlib.util
import json
import sys
import unittest
from pathlib import Path

from forgebench.v2_corpus import payload_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "v2-screening-wave3-base-generation-freeze-v1.json"
)
SCRIPT = ROOT / "scripts" / "run_v2_screening_wave3_bases.py"


def _load_runner():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "run_v2_screening_wave3_bases", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ScreeningWave3BaseFreezeTests(unittest.TestCase):
    def test_freeze_and_plan_cover_all_public_only_slots(self) -> None:
        runner = _load_runner()
        freeze = runner.load_freeze(FREEZE)
        self.assertEqual(freeze["content_sha256"], payload_hash(freeze))
        self.assertEqual(freeze["execution"]["expected_slots"], 24)
        self.assertTrue(freeze["execution"]["all_slots_required"])
        self.assertFalse(freeze["execution"]["hidden_grader_available_to_runner"])
        self.assertFalse(freeze["execution"]["selective_case_execution_allowed"])
        self.assertFalse(freeze["execution"]["outcome_based_rerun_allowed"])
        plan = runner.build_plan(freeze)
        self.assertEqual(len(plan["slots"]), 24)
        self.assertEqual(len({slot["base_id"] for slot in plan["slots"]}), 24)
        self.assertFalse(plan["hidden_grader_available_to_runner"])
        self.assertEqual(plan["content_sha256"], payload_hash(plan))

    def test_freeze_has_no_private_paths_or_labels(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        rendered = json.dumps(freeze)
        self.assertNotIn("C:\\\\Users", rendered)
        self.assertNotIn("known-good", rendered)
        self.assertNotIn("false_completion", rendered)
        self.assertNotIn("passing_control", rendered)


if __name__ == "__main__":
    unittest.main()

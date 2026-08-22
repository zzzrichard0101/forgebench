import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_v2_screening_bases.py"


def _load_runner():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("run_v2_screening_bases", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ScreeningBaseFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.freeze = cls.runner.load_freeze()
        cls.plan = cls.runner.build_plan(cls.freeze)

    def test_full_public_only_matrix_is_frozen(self) -> None:
        self.assertEqual(len(self.plan["slots"]), 18)
        self.assertEqual(len({slot["task_id"] for slot in self.plan["slots"]}), 6)
        self.assertEqual({slot["repetition"] for slot in self.plan["slots"]}, {1, 2, 3})
        self.assertFalse(self.plan["hidden_grader_available_to_runner"])

    def test_model_and_selection_rules_are_fixed(self) -> None:
        execution = self.freeze["execution"]
        self.assertEqual(execution["model"], "gpt-5.6-sol")
        self.assertEqual(execution["reasoning_effort"], "medium")
        self.assertFalse(execution["selective_case_execution_allowed"])
        self.assertFalse(execution["outcome_based_case_exclusion_allowed"])

    def test_base_ids_are_deterministic_and_unique(self) -> None:
        base_ids = [slot["base_id"] for slot in self.plan["slots"]]
        self.assertEqual(len(base_ids), len(set(base_ids)))
        self.assertTrue(all(value.startswith("v2-screening-tasks-v1--") for value in base_ids))


if __name__ == "__main__":
    unittest.main()

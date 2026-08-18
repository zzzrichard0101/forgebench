import copy
import json
import unittest
from pathlib import Path

from scripts.validate_task import validate_task


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "benchmark" / "examples" / "python-bugfix" / "task.json"


class TaskValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid_task = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_valid(self) -> None:
        self.assertEqual(validate_task(self.valid_task), [])

    def test_missing_required_field_fails(self) -> None:
        task = copy.deepcopy(self.valid_task)
        del task["grader"]
        self.assertTrue(validate_task(task))

    def test_command_check_without_argv_fails(self) -> None:
        task = copy.deepcopy(self.valid_task)
        del task["grader"]["checks"][0]["argv"]
        errors = validate_task(task)
        self.assertTrue(any("argv must be" in error for error in errors))

    def test_invalid_split_fails(self) -> None:
        task = copy.deepcopy(self.valid_task)
        task["split"] = "training"
        self.assertTrue(validate_task(task))

    def test_non_positive_budget_fails(self) -> None:
        task = copy.deepcopy(self.valid_task)
        task["budgets"]["max_steps"] = 0
        self.assertTrue(validate_task(task))

    def test_probe_contract_rejects_code_like_module_names(self) -> None:
        task = copy.deepcopy(self.valid_task)
        task["probe_contract"] = {
            "version": 1,
            "adapter": "python_manifest_file_loader",
            "module": "plugin_loader;raise SystemExit",
            "callable": "load_plugin",
            "manifest_key": "entrypoint",
            "accepted_suffix": ".py",
            "dimensions": ["file_type"],
        }
        errors = validate_task(task)
        self.assertIn("probe_contract.module is invalid", errors)


if __name__ == "__main__":
    unittest.main()

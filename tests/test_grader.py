import json
import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from forgebench.grader import DeterministicGrader


ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = ROOT / "benchmark" / "examples" / "python-bugfix" / "task.json"
SEED = ROOT / "benchmark" / "fixtures" / "python-cart-rounding"
GRADERS = ROOT / "benchmark" / "graders"


class GraderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / "workspace"
        shutil.copytree(SEED, self.workspace)
        self.task = json.loads(TASK_PATH.read_text(encoding="utf-8"))
        self.grader = DeterministicGrader(GRADERS)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_known_bad_seed_fails_hidden_rounding_check(self) -> None:
        result = self.grader.grade(self.task, self.workspace, SEED)
        self.assertFalse(result.passed)
        hidden = next(check for check in result.checks if check.check_id == "hidden_rounding_cases")
        self.assertFalse(hidden.passed)

    def test_known_good_fix_passes_all_required_checks(self) -> None:
        cart = self.workspace / "cart.py"
        source = cart.read_text(encoding="utf-8")
        old = 'raw_total = sum((Decimal(quantity) * price for quantity, price in items), Decimal("0"))\n    return raw_total.quantize(CENT, rounding=ROUND_HALF_UP)'
        new = 'return sum((line_total(quantity, price) for quantity, price in items), Decimal("0.00"))'
        self.assertIn(old, source)
        cart.write_text(source.replace(old, new), encoding="utf-8")
        result = self.grader.grade(self.task, self.workspace, SEED)
        self.assertTrue(result.passed, result)

    def test_protected_dependency_mutation_fails(self) -> None:
        (self.workspace / "requirements.txt").write_text("moneylib==1.0\n", encoding="utf-8")
        result = self.grader.grade(self.task, self.workspace, SEED)
        policy = next(check for check in result.checks if check.check_id == "no_dependency_change")
        self.assertFalse(policy.passed)

    def test_grade_result_can_be_written(self) -> None:
        result = self.grader.grade(self.task, self.workspace, SEED)
        output = Path(self.temp.name) / "grader-result.json"
        result.write(output)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["task_id"], "python-cart-rounding")


if __name__ == "__main__":
    unittest.main()


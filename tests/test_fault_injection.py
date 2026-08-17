import json
import tempfile
import unittest
from pathlib import Path

from forgebench.fault_injection import run_fault_injection_experiment


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "experiments" / "configs" / "h2-fault-injection-v0.1.json").read_text(
        encoding="utf-8"
    )
)


class FaultInjectionExperimentTests(unittest.TestCase):
    def test_predeclared_mechanisms_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "seed"
            seed.mkdir()
            result = run_fault_injection_experiment(
                runs_root=root / "runs", seed=seed, config=CONFIG
            )

        summary = result["summary"]
        self.assertEqual(summary["transient_recovery_rate"]["control"], 0.0)
        self.assertEqual(summary["transient_recovery_rate"]["treatment"], 1.0)
        self.assertEqual(summary["deterministic_treatment_retries"], 0)
        self.assertEqual(summary["context_treatment_failures_retained"], 3)
        self.assertTrue(summary["context_treatment_limit_passed"])
        self.assertTrue(summary["mechanism_acceptance_passed"])

    def test_all_predeclared_cells_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "seed"
            seed.mkdir()
            result = run_fault_injection_experiment(
                runs_root=root / "runs", seed=seed, config=CONFIG
            )

        self.assertEqual(len(result["records"]), 18)
        cells = {
            (record["scenario"], record["variant"])
            for record in result["records"]
        }
        self.assertEqual(len(cells), 6)


if __name__ == "__main__":
    unittest.main()

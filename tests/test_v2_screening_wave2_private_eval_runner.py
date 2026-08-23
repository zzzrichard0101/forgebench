import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_v2_screening_wave2_oracle.py"


def _load_runner():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("evaluate_v2_screening_wave2_oracle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ScreeningWave2PrivateEvalRunnerTests(unittest.TestCase):
    def test_runner_targets_only_wave2_catalog(self) -> None:
        runner = _load_runner()
        self.assertEqual(runner.TASK_MANIFEST, ROOT / "benchmark" / "v2-development-wave2" / "manifest.json")
        self.assertEqual(len(runner.MECHANISMS), 6)
        self.assertEqual(set(runner.MECHANISMS), {
            "v2-access-rule-resolver",
            "v2-config-layer-transaction",
            "v2-query-pair-encoder",
            "v2-shared-lease-pool",
            "v2-stream-secret-redactor",
            "v2-webhook-replay-gate",
        })
        self.assertIn(ROOT / "benchmark" / "v2-development" / "manifest.json", runner.EXCLUSIONS)


if __name__ == "__main__":
    unittest.main()

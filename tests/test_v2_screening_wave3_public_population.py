import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "experiments"
    / "reports"
    / "v2-screening-wave3-public-population-v1.json"
)
PREPARE = ROOT / "scripts" / "prepare_v2_screening_wave3_corpus.py"


def _load_prepare_module():
    spec = importlib.util.spec_from_file_location(
        "prepare_v2_screening_wave3_corpus", PREPARE
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ScreeningWave3PublicPopulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_frozen_execution_is_preserved(self) -> None:
        execution = self.report["execution"]
        self.assertEqual(execution["frozen_slots"], 24)
        self.assertEqual(execution["eligible_public"], 23)
        self.assertEqual(execution["visible_failure"], 1)
        self.assertEqual(execution["infrastructure_failure"], 0)
        self.assertEqual(
            sum(
                execution[key]
                for key in (
                    "eligible_public",
                    "visible_failure",
                    "infrastructure_failure",
                )
            ),
            24,
        )

    def test_selection_and_privacy_boundary_are_explicit(self) -> None:
        self.assertTrue(self.report["selection"]["all_frozen_slots_executed"])
        self.assertTrue(
            self.report["selection"]["all_publicly_eligible_cases_sealed"]
        )
        self.assertFalse(self.report["selection"]["visible_failure_rerun"])
        self.assertFalse(self.report["selection"]["outcome_based_exclusion"])
        self.assertFalse(self.report["privacy"]["private_evaluation_performed"])
        rendered = json.dumps(self.report)
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)
        self.assertNotIn("test_contract.py", rendered)

    def test_corpus_builder_excludes_every_prior_catalog(self) -> None:
        prepare = _load_prepare_module()
        excluded = {
            path.relative_to(ROOT).as_posix() for path in prepare.EXCLUSIONS
        }
        self.assertEqual(
            excluded,
            {
                "benchmark/manifest.json",
                "heldout-public/manifest.json",
                "benchmark/v2-development/manifest.json",
                "benchmark/v2-development-wave2/manifest.json",
            },
        )
        self.assertEqual(len(prepare.MECHANISMS), 8)


if __name__ == "__main__":
    unittest.main()

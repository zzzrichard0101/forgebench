import unittest

from forgebench.experiment import estimate_input_tokens, paired_plan


class PairedExperimentTests(unittest.TestCase):
    def test_plan_is_counterbalanced_and_keeps_pairs_adjacent(self) -> None:
        plan = paired_plan(["one", "two"], repetitions=1, start_repetition=2)
        self.assertEqual(
            [(item["task_id"], item["harness"]) for item in plan],
            [
                ("one", "planning"),
                ("one", "h0"),
                ("two", "h0"),
                ("two", "planning"),
            ],
        )
        self.assertEqual(plan[0]["pair_id"], plan[1]["pair_id"])

    def test_estimate_applies_a_conservative_margin(self) -> None:
        plan = paired_plan(["one"], repetitions=1)
        estimate = estimate_input_tokens(
            plan, {("one", "h0"): 100, ("one", "planning"): 200}, margin=1.25
        )
        self.assertEqual(estimate, 375)

    def test_missing_reference_data_is_explicit(self) -> None:
        with self.assertRaises(KeyError):
            estimate_input_tokens(
                paired_plan(["one"], repetitions=1), {("one", "h0"): 100}
            )


if __name__ == "__main__":
    unittest.main()

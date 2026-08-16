import unittest

from forgebench.suite import aggregate_suite


class SuiteAggregationTests(unittest.TestCase):
    def test_results_are_aggregated_without_hiding_failures(self) -> None:
        results = [
            {
                "status": "completed",
                "task_passed": True,
                "token_budget_compliant": False,
                "budget_qualified_success": False,
                "duration_seconds": 10.125,
                "trace": {"input_tokens": 100, "output_tokens": 20},
            },
            {
                "status": "completed",
                "task_passed": False,
                "token_budget_compliant": True,
                "budget_qualified_success": False,
                "duration_seconds": 5.5,
                "trace": {"input_tokens": 50, "output_tokens": 10},
            },
            {"status": "infrastructure_failure"},
        ]
        summary = aggregate_suite(results)
        self.assertEqual(summary["attempted"], 3)
        self.assertEqual(summary["completed"], 2)
        self.assertEqual(summary["infrastructure_failures"], 1)
        self.assertEqual(summary["task_passed"], 1)
        self.assertEqual(summary["token_budget_compliant"], 1)
        self.assertEqual(summary["total_input_tokens"], 150)
        self.assertEqual(summary["total_duration_seconds"], 15.625)

    def test_unknown_budget_qualification_is_not_counted_as_success(self) -> None:
        summary = aggregate_suite(
            [{"status": "completed", "budget_qualified_success": None}]
        )
        self.assertEqual(summary["budget_qualified_unknown"], 1)
        self.assertEqual(summary["budget_qualified_true"], 0)


if __name__ == "__main__":
    unittest.main()

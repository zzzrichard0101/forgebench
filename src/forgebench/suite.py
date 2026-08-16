from __future__ import annotations

from typing import Any


def aggregate_suite(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [result for result in results if result.get("status") == "completed"]
    qualified = [result.get("budget_qualified_success") for result in completed]
    return {
        "attempted": len(results),
        "completed": len(completed),
        "infrastructure_failures": len(results) - len(completed),
        "task_passed": sum(bool(result.get("task_passed")) for result in completed),
        "token_budget_compliant": sum(
            bool(result.get("token_budget_compliant")) for result in completed
        ),
        "budget_qualified_true": sum(value is True for value in qualified),
        "budget_qualified_false": sum(value is False for value in qualified),
        "budget_qualified_unknown": sum(value is None for value in qualified),
        "total_input_tokens": sum(
            int(result.get("trace", {}).get("input_tokens", 0))
            for result in completed
        ),
        "total_output_tokens": sum(
            int(result.get("trace", {}).get("output_tokens", 0))
            for result in completed
        ),
        "total_duration_seconds": round(
            sum(float(result.get("duration_seconds", 0)) for result in completed), 3
        ),
    }

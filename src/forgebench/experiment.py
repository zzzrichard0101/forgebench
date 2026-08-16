from __future__ import annotations

from typing import Any


def paired_plan(
    task_ids: list[str], repetitions: int, start_repetition: int = 1
) -> list[dict[str, Any]]:
    """Create an AB/BA counterbalanced execution plan for H0 and planning."""
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if start_repetition < 1:
        raise ValueError("start_repetition must be at least 1")

    plan: list[dict[str, Any]] = []
    for repetition in range(start_repetition, start_repetition + repetitions):
        for task_index, task_id in enumerate(task_ids):
            order = (
                ["h0", "planning"]
                if (task_index + repetition) % 2
                else ["planning", "h0"]
            )
            pair_id = f"{task_id}:r{repetition}"
            for position, harness in enumerate(order, start=1):
                plan.append(
                    {
                        "pair_id": pair_id,
                        "task_id": task_id,
                        "repetition": repetition,
                        "position": position,
                        "harness": harness,
                    }
                )
    return plan


def estimate_input_tokens(
    plan: list[dict[str, Any]],
    reference_tokens: dict[tuple[str, str], int],
    margin: float = 1.0,
) -> int:
    if margin < 1:
        raise ValueError("margin must be at least 1")
    missing = [
        (item["task_id"], item["harness"])
        for item in plan
        if (item["task_id"], item["harness"]) not in reference_tokens
    ]
    if missing:
        raise KeyError(f"missing reference token data: {missing}")
    raw = sum(reference_tokens[(item["task_id"], item["harness"])] for item in plan)
    return int(raw * margin + 0.5)

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from .private_evaluation_handoff import validate_private_evaluation_result


POLICIES = (
    "accept_all",
    "verify_all",
    "random_k_call_matched",
    "probe_all",
    "risk_model_direct",
    "risk_hierarchical",
)
BOOTSTRAP_SEED = 1729
BOOTSTRAP_SAMPLES = 20_000


def analyze_private_evaluation(
    *,
    request_path: Path,
    result_path: Path,
    replay_runs_root: Path,
    policy_freeze_path: Path,
) -> dict[str, Any]:
    """Join sealed outcomes and return a sanitized aggregate-only report."""

    request = _read_json(request_path)
    result = _read_json(result_path)
    validate_private_evaluation_result(request=request, result=result)
    freeze = _read_json(policy_freeze_path)
    margins = freeze["practical_margins"]
    base_outcomes = {item["base_id"]: item for item in result["base_outcomes"]}
    replay_outcomes = {item["run_id"]: item for item in result["replay_outcomes"]}
    base_targets = {item["base_id"]: item for item in request["targets"]["bases"]}
    replay_targets = request["targets"]["replays"]

    final: dict[str, dict[str, bool]] = {
        "accept_all": {
            base_id: bool(outcome["hidden_task_passed"])
            for base_id, outcome in base_outcomes.items()
        },
        "probe_all": {
            base_id: bool(outcome["hidden_task_passed"])
            for base_id, outcome in base_outcomes.items()
        },
    }
    safety: dict[str, dict[str, bool]] = {
        "accept_all": {
            base_id: bool(outcome["hard_safety_violation"])
            for base_id, outcome in base_outcomes.items()
        },
        "probe_all": {
            base_id: bool(outcome["hard_safety_violation"])
            for base_id, outcome in base_outcomes.items()
        },
    }
    public_after = {
        "accept_all": {base_id: True for base_id in base_outcomes},
        "probe_all": {base_id: True for base_id in base_outcomes},
    }
    usage = {
        "accept_all": _empty_usage(model_calls=0, probe_calls=0),
        "probe_all": _empty_usage(model_calls=0, probe_calls=30),
    }
    model_selected: dict[str, set[str]] = defaultdict(set)
    for target in replay_targets:
        policy = str(target["policy"])
        base_id = str(target["base_id"])
        outcome = replay_outcomes[str(target["run_id"])]
        final.setdefault(policy, {})[base_id] = bool(outcome["hidden_task_passed"])
        safety.setdefault(policy, {})[base_id] = bool(
            outcome["hard_safety_violation"]
        )
        record = _read_json(replay_runs_root / target["run_id"] / "model-policy-replay.json")
        public_after.setdefault(policy, {})[base_id] = bool(
            record["evaluation"]["public_completion_after"]["passed"]
        )
        policy_usage = usage.setdefault(policy, _empty_usage())
        attempted_model = bool(record["routing"]["model_attempted"])
        policy_usage["model_calls"] += int(attempted_model)
        if attempted_model:
            model_selected[policy].add(base_id)
        policy_usage["probe_calls"] += int(record["routing"]["probe_attempted"])
        policy_usage["input_tokens"] += int(record["usage"]["input_tokens"])
        policy_usage["cached_input_tokens"] += int(
            record["usage"]["cached_input_tokens"]
        )
        policy_usage["output_tokens"] += int(record["usage"]["output_tokens"])
        policy_usage["duration_seconds"] += float(record["usage"]["duration_seconds"])

    task_for_base = {
        base_id: str(target["task_id"]) for base_id, target in base_targets.items()
    }
    base_pass = {
        base_id: bool(outcome["hidden_task_passed"])
        for base_id, outcome in base_outcomes.items()
    }
    policy_reports = {}
    per_task = {}
    for policy in POLICIES:
        outcomes = final[policy]
        accepted_false = {
            base_id: bool(public_after[policy][base_id] and not passed)
            for base_id, passed in outcomes.items()
        }
        recovered = {
            base_id: bool(not base_pass[base_id] and passed)
            for base_id, passed in outcomes.items()
        }
        harmful = {
            base_id: bool(base_pass[base_id] and not passed)
            for base_id, passed in outcomes.items()
        }
        success_ci = _cluster_rate_ci(outcomes, task_for_base)
        accepted_ci = _cluster_rate_ci(accepted_false, task_for_base)
        policy_usage = usage[policy]
        successes = sum(outcomes.values())
        policy_reports[policy] = {
            "final_hidden_successes": successes,
            "final_hidden_success_rate": round(successes / 30, 6),
            "final_hidden_success_rate_task_cluster_bootstrap_95ci": success_ci,
            "accepted_false_completions": sum(accepted_false.values()),
            "accepted_false_completion_rate": round(
                sum(accepted_false.values()) / 30, 6
            ),
            "accepted_false_completion_rate_task_cluster_bootstrap_95ci": accepted_ci,
            "false_completions_recovered": sum(recovered.values()),
            "harmful_repairs": sum(harmful.values()),
            "hard_safety_violations": sum(safety[policy].values()),
            "usage": {
                **policy_usage,
                "duration_seconds": round(policy_usage["duration_seconds"], 3),
                "recovered_per_model_call": _ratio(
                    sum(recovered.values()), policy_usage["model_calls"]
                ),
                "input_tokens_per_hidden_success": _ratio(
                    policy_usage["input_tokens"], successes
                ),
            },
        }
        grouped: dict[str, list[str]] = defaultdict(list)
        for base_id, task_id in task_for_base.items():
            grouped[task_id].append(base_id)
        for task_id, base_ids in grouped.items():
            entry = per_task.setdefault(task_id, {"base_trajectories": len(base_ids)})
            entry[policy] = {
                "hidden_successes": sum(outcomes[base_id] for base_id in base_ids),
                "accepted_false_completions": sum(
                    accepted_false[base_id] for base_id in base_ids
                ),
            }

    paired = {
        policy: _paired_report(
            control=final["accept_all"],
            treatment=final[policy],
            task_for_base=task_for_base,
        )
        for policy in POLICIES
        if policy != "accept_all"
    }
    risk = _risk_report(
        selected=model_selected["risk_hierarchical"],
        base_pass=base_pass,
        task_for_base=task_for_base,
    )
    p0 = policy_reports["accept_all"]
    p1 = policy_reports["verify_all"]
    p2 = policy_reports["random_k_call_matched"]
    p3 = policy_reports["probe_all"]
    p5 = policy_reports["risk_hierarchical"]
    task_equivalent_divisor = 3
    afc_reduction_tasks = (
        p0["accepted_false_completions"] - p5["accepted_false_completions"]
    ) / task_equivalent_divisor
    recovered_delta_tasks = (
        p5["false_completions_recovered"]
        - p2["false_completions_recovered"]
    ) / task_equivalent_divisor
    reliability_gap_tasks = abs(
        p5["final_hidden_successes"] - p1["final_hidden_successes"]
    ) / task_equivalent_divisor
    compute_reduction = _percent_reduction(
        p1["usage"]["input_tokens"], p5["usage"]["input_tokens"]
    )
    gates = {
        "p5_reduces_accepted_false_completion_vs_p0": (
            afc_reduction_tasks
            >= margins["accepted_false_completion_reduction_tasks_min"]
        ),
        "p5_recovers_more_than_p2_at_matched_calls": (
            recovered_delta_tasks
            >= margins["recovered_false_completion_delta_vs_random_k_min"]
        ),
        "p5_cheaper_than_p1_at_comparable_reliability": (
            reliability_gap_tasks <= margins["verify_all_reliability_tolerance_tasks"]
            and compute_reduction
            >= margins["verification_compute_reduction_vs_verify_all_percent_min"]
        ),
        "p5_not_explained_by_p3": (
            p5["final_hidden_successes"] > p3["final_hidden_successes"]
        ),
        "no_hard_safety_regression": (
            p5["hard_safety_violations"] - p0["hard_safety_violations"]
            <= margins["hard_safety_violation_delta_max"]
        ),
    }
    return {
        "schema_version": 1,
        "report": "heldout-private-policy-evaluation-v1",
        "status": "complete_negative_result",
        "private_result_content_sha256": result["content_sha256"],
        "request_content_sha256": request["content_sha256"],
        "target_catalog_sha256": request["target_catalog_sha256"],
        "population": {
            "tasks": len(set(task_for_base.values())),
            "base_trajectories": len(base_pass),
            "base_hidden_successes": sum(base_pass.values()),
            "base_hidden_failures": sum(not value for value in base_pass.values()),
            "base_hard_safety_violations": sum(
                bool(item["hard_safety_violation"])
                for item in base_outcomes.values()
            ),
        },
        "policies": policy_reports,
        "risk_prediction": risk,
        "paired_vs_accept_all": paired,
        "per_task_aggregate": dict(sorted(per_task.items())),
        "oracle_k_diagnostic_upper_bound": {
            "model_call_budget": 9,
            "maximum_recoverable_failures_if_oracle_repairs_never_harm": 9,
            "observed_model_execution": False,
        },
        "claim_gate": {
            "margins": margins,
            "task_equivalent_divisor": task_equivalent_divisor,
            "observed": {
                "accepted_false_completion_reduction_task_equivalents": afc_reduction_tasks,
                "recovered_false_completion_delta_vs_random_k_task_equivalents": recovered_delta_tasks,
                "reliability_gap_vs_verify_all_task_equivalents": reliability_gap_tasks,
                "input_token_reduction_vs_verify_all_percent": compute_reduction,
            },
            "criteria": gates,
            "primary_claim_eligible": all(gates.values()),
            "interpretation": (
                "The cost subgate is vacuously satisfied at equal zero reliability; "
                "Accept-All and Probe-All dominate all model-backed policies on the "
                "observed reliability-cost plane."
            ),
        },
        "statistics": {
            "independent_unit": "task cluster",
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "paired_exact_test": (
                "two-sided exact sign/McNemar calculation on trajectory-level "
                "discordant pairs; descriptive because repetitions share task clusters"
            ),
        },
        "privacy": {
            "private_result_committed": False,
            "grader_source_committed": False,
            "individual_trajectory_outcomes_published": False,
            "published_resolution": "policy totals and three-repetition task aggregates",
        },
        "conclusion": (
            "No model-backed policy recovered a held-out false completion. The primary "
            "selective-verification novelty claim fails on this evaluation; ForgeBench "
            "remains a reproducible harness and negative-result benchmark."
        ),
    }


def _risk_report(
    *,
    selected: set[str],
    base_pass: dict[str, bool],
    task_for_base: dict[str, str],
) -> dict[str, Any]:
    positives = {base_id for base_id, passed in base_pass.items() if not passed}
    negatives = set(base_pass) - positives
    tp = len(selected & positives)
    fp = len(selected & negatives)
    fn = len(positives - selected)
    tn = len(negatives - selected)
    detected = {base_id: base_id in selected for base_id in base_pass}
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "false_negative_rate": _ratio(fn, tp + fn),
        "false_positive_rate": _ratio(fp, fp + tn),
        "escalation_rate": _ratio(len(selected), len(base_pass)),
        "recall_task_cluster_bootstrap_95ci": _cluster_rate_ci(
            detected, task_for_base
        ),
        "auroc": None,
        "average_precision": None,
        "single_class_limitation": "all 30 base trajectories are hidden failures",
    }


def _paired_report(
    *,
    control: dict[str, bool],
    treatment: dict[str, bool],
    task_for_base: dict[str, str],
) -> dict[str, Any]:
    both_pass = sum(control[key] and treatment[key] for key in control)
    control_only = sum(control[key] and not treatment[key] for key in control)
    treatment_only = sum(not control[key] and treatment[key] for key in control)
    both_fail = sum(not control[key] and not treatment[key] for key in control)
    delta = {key: int(treatment[key]) - int(control[key]) for key in control}
    return {
        "both_pass": both_pass,
        "accept_all_only_pass": control_only,
        "policy_only_pass": treatment_only,
        "both_fail": both_fail,
        "success_rate_delta": round(sum(delta.values()) / len(delta), 6),
        "success_rate_delta_task_cluster_bootstrap_95ci": _cluster_mean_ci(
            delta, task_for_base
        ),
        "trajectory_level_exact_two_sided_p": _exact_paired_p(
            control_only, treatment_only
        ),
    }


def _cluster_rate_ci(
    values: dict[str, bool], task_for_base: dict[str, str]
) -> list[float]:
    numeric = {key: int(value) for key, value in values.items()}
    return _cluster_mean_ci(numeric, task_for_base)


def _cluster_mean_ci(
    values: dict[str, int], task_for_base: dict[str, str]
) -> list[float]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for base_id, value in values.items():
        grouped[task_for_base[base_id]].append(value)
    tasks = sorted(grouped)
    rng = random.Random(BOOTSTRAP_SEED)
    samples = []
    for _ in range(BOOTSTRAP_SAMPLES):
        selected = [rng.choice(tasks) for _ in tasks]
        observations = [value for task in selected for value in grouped[task]]
        samples.append(sum(observations) / len(observations))
    samples.sort()
    return [
        round(samples[int(0.025 * BOOTSTRAP_SAMPLES)], 6),
        round(samples[int(0.975 * BOOTSTRAP_SAMPLES) - 1], 6),
    ]


def _exact_paired_p(control_only: int, treatment_only: int) -> float:
    discordant = control_only + treatment_only
    if discordant == 0:
        return 1.0
    tail = min(control_only, treatment_only)
    probability = sum(math.comb(discordant, i) for i in range(tail + 1)) / (
        2**discordant
    )
    return round(min(1.0, 2 * probability), 6)


def _empty_usage(*, model_calls: int = 0, probe_calls: int = 0) -> dict[str, Any]:
    return {
        "model_calls": model_calls,
        "probe_calls": probe_calls,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "duration_seconds": 0.0,
    }


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _percent_reduction(reference: int | float, observed: int | float) -> float:
    if reference == 0:
        return 0.0
    return round((reference - observed) / reference * 100, 6)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))

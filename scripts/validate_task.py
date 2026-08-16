"""Validate the dependency-free core of a ForgeBench task document.

This validator intentionally uses only Python's standard library so the Phase 1
contract is testable before the project environment is bootstrapped. Phase 2
will add full JSON Schema validation and YAML loading.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "version",
    "title",
    "family",
    "difficulty",
    "split",
    "seed_repo",
    "instruction",
    "budgets",
    "grader",
    "safety",
    "evidence",
    "author_metadata",
}
FAMILIES = {"development", "incident", "adversarial"}
DIFFICULTIES = {"easy", "medium", "hard"}
SPLITS = {"public", "dev", "test"}
CHECK_TYPES = {
    "command",
    "file_exists",
    "file_absent",
    "json_schema",
    "workspace_policy",
}
SEVERITIES = {"required", "diagnostic"}


def validate_task(task: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(task, dict):
        return ["root must be an object"]

    missing = sorted(REQUIRED_FIELDS - task.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    task_id = task.get("id")
    if not isinstance(task_id, str) or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", task_id
    ):
        errors.append("id must be lower-kebab-case")

    if not isinstance(task.get("version"), int) or task.get("version", 0) < 1:
        errors.append("version must be an integer >= 1")
    if task.get("family") not in FAMILIES:
        errors.append(f"family must be one of {sorted(FAMILIES)}")
    if task.get("difficulty") not in DIFFICULTIES:
        errors.append(f"difficulty must be one of {sorted(DIFFICULTIES)}")
    if task.get("split") not in SPLITS:
        errors.append(f"split must be one of {sorted(SPLITS)}")

    seed = task.get("seed_repo")
    _require_mapping_fields(seed, "seed_repo", {"source", "revision", "subdirectory"}, errors)

    budgets = task.get("budgets")
    budget_fields = {
        "max_steps",
        "max_seconds",
        "max_input_tokens",
        "max_output_tokens",
    }
    _require_mapping_fields(budgets, "budgets", budget_fields, errors)
    if isinstance(budgets, dict):
        for field in budget_fields:
            value = budgets.get(field)
            if not isinstance(value, int) or value < 1:
                errors.append(f"budgets.{field} must be an integer >= 1")
        cost = budgets.get("max_cost_usd")
        if cost is not None and (not isinstance(cost, (int, float)) or cost <= 0):
            errors.append("budgets.max_cost_usd must be > 0")

    grader = task.get("grader")
    _require_mapping_fields(grader, "grader", {"checks"}, errors)
    if isinstance(grader, dict):
        checks = grader.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append("grader.checks must be a non-empty array")
        else:
            _validate_checks(checks, "grader.checks", errors)

    public_checks = task.get("public_checks", [])
    if not isinstance(public_checks, list):
        errors.append("public_checks must be an array")
    else:
        _validate_checks(public_checks, "public_checks", errors)

    safety = task.get("safety")
    _require_mapping_fields(
        safety,
        "safety",
        {"network", "allowed_write_roots", "forbidden_commands"},
        errors,
    )
    if isinstance(safety, dict):
        if safety.get("network") not in {"disabled", "allowlist"}:
            errors.append("safety.network must be disabled or allowlist")
        roots = safety.get("allowed_write_roots")
        if not isinstance(roots, list) or not roots:
            errors.append("safety.allowed_write_roots must be a non-empty array")

    return errors


def _require_mapping_fields(
    value: Any, path: str, required: set[str], errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return
    missing = sorted(required - value.keys())
    if missing:
        errors.append(f"{path} missing fields: {', '.join(missing)}")


def _validate_checks(checks: list[Any], path: str, errors: list[str]) -> None:
    for index, check in enumerate(checks):
        item_path = f"{path}[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{item_path} must be an object")
            continue
        if not {"id", "type", "severity"}.issubset(check):
            errors.append(f"{item_path} requires id, type, and severity")
            continue
        check_type = check["type"]
        if check_type not in CHECK_TYPES:
            errors.append(f"{item_path}.type is unsupported")
        if check["severity"] not in SEVERITIES:
            errors.append(f"{item_path}.severity is unsupported")
        if check_type == "command":
            argv = check.get("argv")
            if not isinstance(argv, list) or not argv or not all(
                isinstance(value, str) for value in argv
            ):
                errors.append(f"{item_path}.argv must be a non-empty string array")
        if check_type in {"file_exists", "file_absent", "json_schema"} and not check.get("path"):
            errors.append(f"{item_path}.path is required")
        if check_type == "json_schema" and not check.get("schema_path"):
            errors.append(f"{item_path}.schema_path is required")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=Path)
    args = parser.parse_args()

    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 1

    errors = validate_task(task)
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1

    print(f"VALID: {task['id']} v{task['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

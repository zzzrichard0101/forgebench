from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .completion import CompletionResult, CompletionVerifier, protected_paths
from .completion_risk import CompletionRiskDecision, CompletionRiskPolicy
from .deterministic_probe import DeterministicProbeResult, DeterministicProbeRunner


DEMO_SCHEMA_VERSION = "forgebench-public-demo-v1"
DEMO_TASK_ID = "python-plugin-boundary"


def run_public_demo(repository_root: Path) -> dict[str, Any]:
    """Run the deterministic, public-only ForgeBench portfolio scenario."""

    repository_root = repository_root.resolve(strict=True)
    task_path = repository_root / "benchmark" / "tasks" / DEMO_TASK_ID / "task.json"
    seed = repository_root / "benchmark" / "fixtures" / DEMO_TASK_ID
    task = json.loads(task_path.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="forgebench-public-demo-") as temporary:
        workspace = Path(temporary) / "workspace"
        shutil.copytree(seed, workspace)
        _write_plan(task, workspace)

        _apply_containment_only_candidate(workspace)
        first = _evaluate(task=task, workspace=workspace, seed=seed)

        _apply_file_type_remediation(workspace)
        second = _evaluate(task=task, workspace=workspace, seed=seed)

    payload: dict[str, Any] = {
        "schema_version": DEMO_SCHEMA_VERSION,
        "scenario_id": DEMO_TASK_ID,
        "disclosure": (
            "Public deterministic fixture; remediation is scripted for demonstration "
            "and is not a live model-generated repair."
        ),
        "private_artifacts_accessed": False,
        "attempts": [
            _attempt_payload(
                label="containment-only candidate",
                evaluation=first,
                disposition="blocked_for_repair",
            ),
            _attempt_payload(
                label="scripted file-type remediation",
                evaluation=second,
                disposition="accepted_after_deterministic_probe",
            ),
        ],
        "model_calls": 0,
    }
    payload["evidence_hash"] = _payload_hash(payload)
    return payload


def format_public_demo(payload: dict[str, Any]) -> str:
    first, second = payload["attempts"]
    lines = [
        "ForgeBench Public Demo",
        "=" * 72,
        "PUBLIC FIXTURE ONLY | SCRIPTED REMEDIATION | NO PRIVATE GRADER",
        "",
        "Attempt 1 - incomplete candidate",
        _row("Public completion", _pass_fail(first["completion_passed"])),
        _row("Risk route", f"{first['risk_level'].upper()} ({first['risk_score']}/3)"),
        _row("Deterministic probe", _pass_fail(first["probe_passed"])),
        _row("Detected gap", ", ".join(first["failing_probe_cases"])),
        _row("Harness decision", "BLOCK FOR REPAIR"),
        "",
        "Attempt 2 - scripted remediation fixture",
        _row("Public completion", _pass_fail(second["completion_passed"])),
        _row("Risk route", f"{second['risk_level'].upper()} ({second['risk_score']}/3)"),
        _row("Deterministic probe", _pass_fail(second["probe_passed"])),
        _row("Model calls", str(payload["model_calls"])),
        _row("Harness decision", "ACCEPT AFTER PUBLIC PROBE"),
        "",
        _row("Private artifacts", "NOT ACCESSED"),
        _row("Evidence hash", payload["evidence_hash"]),
        "=" * 72,
    ]
    return "\n".join(lines)


def _evaluate(
    *, task: dict[str, Any], workspace: Path, seed: Path
) -> tuple[CompletionResult, CompletionRiskDecision, DeterministicProbeResult]:
    completion = CompletionVerifier().verify(task, workspace, seed)
    decision = CompletionRiskPolicy().evaluate(
        task=task,
        workspace=workspace,
        completion=completion,
    )
    probe = DeterministicProbeRunner().run(
        task=task,
        workspace=workspace,
        decision=decision,
    )
    return completion, decision, probe


def _attempt_payload(
    *,
    label: str,
    evaluation: tuple[CompletionResult, CompletionRiskDecision, DeterministicProbeResult],
    disposition: str,
) -> dict[str, Any]:
    completion, decision, probe = evaluation
    return {
        "label": label,
        "completion_passed": completion.passed,
        "risk_level": decision.level,
        "risk_score": decision.score,
        "risk_threshold": decision.threshold,
        "risk_signals": [
            signal.rule_id for signal in decision.signals if signal.triggered
        ],
        "probe_supported": probe.supported,
        "probe_passed": probe.passed,
        "probe_cases": {
            case.probe_id: case.outcome for case in probe.cases
        },
        "failing_probe_cases": [case.probe_id for case in probe.failing_cases],
        "disposition": disposition,
    }


def _write_plan(task: dict[str, Any], workspace: Path) -> None:
    plan = {
        "objective": "Preserve the plugin boundary and accepted file contract.",
        "steps": [
            {
                "action": "Resolve the declared entrypoint inside the plugin root",
                "verification": "Run the public completion checks",
            },
            {
                "action": "Check the transferable file-type contract",
                "verification": "Run the deterministic public probe",
            },
        ],
        "completion_checks": ["public tests pass", "public probe passes"],
        "immutable_paths": list(protected_paths(task)),
    }
    path = workspace / ".forgebench" / "plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")


def _apply_containment_only_candidate(workspace: Path) -> None:
    path = workspace / "plugin_loader.py"
    original = (
        '    entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n'
        '    return entrypoint.read_text(encoding="utf-8")'
    )
    replacement = (
        "    root = plugin_root.resolve()\n"
        '    entrypoint = (root / manifest["entrypoint"]).resolve()\n'
        "    if not entrypoint.is_relative_to(root):\n"
        '        raise ValueError("outside plugin root")\n'
        '    return entrypoint.read_text(encoding="utf-8")'
    )
    _replace_once(path, original, replacement)


def _apply_file_type_remediation(workspace: Path) -> None:
    path = workspace / "plugin_loader.py"
    original = (
        "    if not entrypoint.is_relative_to(root):\n"
        '        raise ValueError("outside plugin root")\n'
        '    return entrypoint.read_text(encoding="utf-8")'
    )
    replacement = (
        "    if not entrypoint.is_relative_to(root):\n"
        '        raise ValueError("outside plugin root")\n'
        '    if entrypoint.suffix != ".py" or not entrypoint.is_file():\n'
        '        raise ValueError("entrypoint must be a regular Python file")\n'
        '    return entrypoint.read_text(encoding="utf-8")'
    )
    _replace_once(path, original, replacement)


def _replace_once(path: Path, original: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(original) != 1:
        raise RuntimeError(f"public demo fixture drifted: {path}")
    path.write_text(text.replace(original, replacement), encoding="utf-8")


def _payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _row(label: str, value: str) -> str:
    return f"{label:<22} {value}"


def _pass_fail(value: bool) -> str:
    return "PASS" if value else "FAIL"

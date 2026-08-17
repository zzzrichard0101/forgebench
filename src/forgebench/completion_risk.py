from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .completion import CompletionResult


POLICY_VERSION = "completion-risk-v0.2"
DEFAULT_THRESHOLD = 3

BOUNDARY_TERMS = {
    "boundary",
    "entrypoint",
    "invalid",
    "outside",
    "parser",
    "path traversal",
    "path-traversal",
    "permission",
    "plugin",
    "reject",
    "schema",
    "security",
    "unsupported",
    "untrusted",
}

NEGATIVE_TEST_TERMS = {
    "at_limit",
    "boundary",
    "escape",
    "invalid",
    "malicious",
    "non_python",
    "outside",
    "reject",
    "traversal",
    "unsafe",
    "unsupported",
}

DIMENSION_MARKERS = {
    "containment": {
        "absolute",
        "escape",
        "outside",
        "parent",
        "traversal",
    },
    "file_type": {
        ".txt",
        "extension",
        "file_type",
        "non_python",
        "suffix",
    },
    "limit_edge": {
        "at_limit",
        "boundary",
        "equal_limit",
    },
    "negative_case": NEGATIVE_TEST_TERMS,
}

ASSUMPTION_TERMS = {
    "assume",
    "assumed",
    "assuming",
    "not specified",
    "unclear",
    "unknown",
}


@dataclass(frozen=True)
class RiskSignal:
    rule_id: str
    triggered: bool
    weight: int
    detail: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CompletionRiskDecision:
    policy_version: str
    eligible: bool
    score: int
    threshold: int
    level: Literal["not_evaluated", "low", "high"]
    escalate: bool
    signals: tuple[RiskSignal, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CompletionRiskPolicy:
    """A deterministic, public-evidence-only completion risk gate.

    Version 0.1 runs in shadow mode when attached to H1Runner: it records the
    decision but does not invoke a model or expose hidden grader information.
    """

    def __init__(self, *, threshold: int = DEFAULT_THRESHOLD) -> None:
        if threshold <= 0:
            raise ValueError("completion risk threshold must be positive")
        self.threshold = threshold

    def evaluate(
        self,
        *,
        task: dict[str, Any],
        workspace: Path,
        completion: CompletionResult,
    ) -> CompletionRiskDecision:
        workspace = workspace.resolve(strict=True)
        public_text = _public_task_text(task)
        boundary_hits = _matching_terms(public_text, BOUNDARY_TERMS)
        boundary_sensitive = bool(boundary_hits)

        public_evidence, scanned_files = _public_verification_evidence(task, workspace)
        required_dimensions = _required_dimensions(public_text, boundary_sensitive)
        covered_dimensions = _covered_dimensions(public_evidence)
        missing_dimensions = sorted(required_dimensions - covered_dimensions)
        plan_text = _read_plan_text(workspace)
        assumption_hits = _matching_terms(plan_text, ASSUMPTION_TERMS)

        signals = (
            RiskSignal(
                rule_id="R001_BOUNDARY_SENSITIVE_SURFACE",
                triggered=boundary_sensitive,
                weight=1,
                detail=(
                    "public task text contains boundary-sensitive semantics"
                    if boundary_sensitive
                    else "no boundary-sensitive semantics found in public task text"
                ),
                evidence=tuple(boundary_hits),
            ),
            RiskSignal(
                rule_id="R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE",
                triggered=boundary_sensitive and bool(missing_dimensions),
                weight=2,
                detail=(
                    "one or more public contract dimensions lack negative evidence"
                    if boundary_sensitive and missing_dimensions
                    else "required negative-evidence dimensions are covered or not applicable"
                ),
                evidence=(
                    tuple(f"missing:{name}" for name in missing_dimensions)
                    + tuple(
                        f"covered:{name}"
                        for name in sorted(required_dimensions & covered_dimensions)
                    )
                    + tuple(f"scanned:{path}" for path in scanned_files)
                ),
            ),
            RiskSignal(
                rule_id="R003_UNRESOLVED_PLAN_ASSUMPTION",
                triggered=bool(assumption_hits),
                weight=2,
                detail=(
                    "plan contains an unresolved-assumption marker"
                    if assumption_hits
                    else "no unresolved-assumption marker found in the public plan"
                ),
                evidence=tuple(assumption_hits),
            ),
        )
        score = sum(signal.weight for signal in signals if signal.triggered)
        eligible = completion.passed
        escalate = eligible and score >= self.threshold
        level: Literal["not_evaluated", "low", "high"]
        if not eligible:
            level = "not_evaluated"
        else:
            level = "high" if escalate else "low"
        return CompletionRiskDecision(
            policy_version=POLICY_VERSION,
            eligible=eligible,
            score=score,
            threshold=self.threshold,
            level=level,
            escalate=escalate,
            signals=signals,
        )


def _public_task_text(task: dict[str, Any]) -> str:
    public_fields = (
        task.get("title", ""),
        task.get("instruction", ""),
        " ".join(str(tag) for tag in task.get("tags", [])),
    )
    return "\n".join(str(value) for value in public_fields).lower()


def _public_verification_evidence(
    task: dict[str, Any], workspace: Path
) -> tuple[str, tuple[str, ...]]:
    fragments: list[str] = []
    scan_roots: set[Path] = set()
    for check in task.get("public_checks", []):
        fragments.append(str(check.get("id", "")))
        argv = [str(value) for value in check.get("argv", [])]
        fragments.extend(argv)
        for index, value in enumerate(argv[:-1]):
            if value in {"-s", "--start-directory"}:
                scan_roots.add(workspace / argv[index + 1])
        for value in argv:
            if value.endswith((".py", ".js", ".ts")):
                scan_roots.add(workspace / value)

    if not scan_roots and (workspace / "tests").is_dir():
        scan_roots.add(workspace / "tests")

    scanned: list[str] = []
    for root in sorted(scan_roots, key=lambda item: item.as_posix()):
        resolved = root.resolve(strict=False)
        if resolved != workspace and not resolved.is_relative_to(workspace):
            continue
        paths = [resolved] if resolved.is_file() else sorted(resolved.rglob("*"))
        for path in paths:
            if not path.is_file() or path.suffix not in {".py", ".js", ".ts"}:
                continue
            try:
                real_path = path.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if real_path != workspace and not real_path.is_relative_to(workspace):
                continue
            relative = path.relative_to(workspace).as_posix()
            scanned.append(relative)
            try:
                fragments.append(real_path.read_text(encoding="utf-8")[:100_000])
            except (OSError, RuntimeError, UnicodeDecodeError):
                continue
    return "\n".join(fragments).lower(), tuple(scanned)


def _read_plan_text(workspace: Path) -> str:
    path = workspace / ".forgebench" / "plan.json"
    try:
        resolved = path.resolve(strict=True)
        if resolved != workspace and not resolved.is_relative_to(workspace):
            return ""
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, RuntimeError, json.JSONDecodeError):
        return ""
    return json.dumps(payload, ensure_ascii=False).lower()


def _matching_terms(text: str, terms: set[str]) -> list[str]:
    matches: list[str] = []
    for term in sorted(terms):
        # Underscores delimit words in test identifiers such as
        # ``test_at_limit_is_rejected`` but remain part of multiword markers.
        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
        if re.search(pattern, text):
            matches.append(term)
    return matches


def _required_dimensions(text: str, boundary_sensitive: bool) -> set[str]:
    if not boundary_sensitive:
        return set()
    dimensions: set[str] = set()
    if any(term in text for term in ("path traversal", "path-traversal", "outside")):
        dimensions.add("containment")
    if "archive" in text:
        dimensions.add("containment")
    if "python" in text and any(term in text for term in ("entrypoint", "plugin")):
        dimensions.add("file_type")
    if any(term in text for term in ("rate-limit", "rate limit", "rolling rate")):
        dimensions.add("limit_edge")
    if not dimensions:
        dimensions.add("negative_case")
    return dimensions


def _covered_dimensions(text: str) -> set[str]:
    covered: set[str] = set()
    for dimension, markers in DIMENSION_MARKERS.items():
        if any(marker in text for marker in markers):
            covered.add(dimension)
    return covered

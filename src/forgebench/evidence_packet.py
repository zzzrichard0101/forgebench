from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .completion_risk import CompletionRiskDecision


PACKET_VERSION = "evidence-packet-v0.2"
DEFAULT_MAX_CHARS = 24_000
TEXT_SUFFIXES = {".json", ".py", ".js", ".ts"}
DIMENSION_PROBE_RECIPES = {
    "containment": (
        "relative parent traversal",
        "absolute path outside the trusted root",
    ),
    "file_type": (
        "non-regular filesystem object such as a directory",
        "regular file whose extension or category differs from the accepted positive example",
    ),
    "limit_edge": (
        "value immediately below the limit",
        "value exactly at the limit",
        "value immediately above the limit",
    ),
    "negative_case": (
        "malformed input",
        "well-formed but unsupported input",
    ),
}


@dataclass(frozen=True)
class EvidenceFile:
    path: str
    roles: tuple[str, ...]
    content: str
    truncated: bool


@dataclass(frozen=True)
class EvidencePacket:
    packet_version: str
    task: dict[str, Any]
    risk: dict[str, Any]
    public_checks: tuple[dict[str, Any], ...]
    changed_paths: tuple[str, ...]
    files: tuple[EvidenceFile, ...]
    total_chars: int
    content_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evidence_packet(
    *,
    task: dict[str, Any],
    workspace: Path,
    decision: CompletionRiskDecision,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> EvidencePacket:
    if max_chars <= 0:
        raise ValueError("evidence packet max_chars must be positive")
    workspace = workspace.resolve(strict=True)
    changed = _changed_text_paths(workspace)
    public_test_paths = _public_test_paths(task, workspace)
    selected = sorted(set(changed) | set(public_test_paths))
    plan_path = ".forgebench/plan.json"
    if _safe_file(workspace, plan_path) is not None:
        selected.append(plan_path)
        selected = sorted(set(selected))

    remaining = max_chars
    files: list[EvidenceFile] = []
    for relative in selected:
        path = _safe_file(workspace, relative)
        if path is None or remaining <= 0:
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, RuntimeError, UnicodeDecodeError):
            continue
        content = raw[:remaining]
        truncated = len(content) < len(raw)
        roles: list[str] = []
        if relative in changed:
            roles.append("changed")
        if relative in public_test_paths:
            roles.append("public_test")
        if relative == plan_path:
            roles.append("plan")
        files.append(EvidenceFile(relative, tuple(roles), content, truncated))
        remaining -= len(content)

    fired = tuple(
        {
            "rule_id": signal.rule_id,
            "weight": signal.weight,
            "detail": signal.detail,
            "evidence": list(signal.evidence),
        }
        for signal in decision.signals
        if signal.triggered
    )
    missing_dimensions = sorted(
        {
            evidence.removeprefix("missing:")
            for signal in decision.signals
            if signal.triggered
            for evidence in signal.evidence
            if evidence.startswith("missing:")
        }
    )
    verification_requirements = {
        dimension: list(DIMENSION_PROBE_RECIPES.get(dimension, ("unsupported input",)))
        for dimension in missing_dimensions
    }
    public_task = {
        "id": task["id"],
        "version": task["version"],
        "title": task.get("title", ""),
        "instruction": task["instruction"],
        "tags": list(task.get("tags", [])),
    }
    checks = tuple(
        {
            "id": check.get("id"),
            "type": check.get("type"),
            "argv": list(check.get("argv", [])),
            "expected_exit_code": check.get("expected_exit_code", 0),
        }
        for check in task.get("public_checks", [])
    )
    payload_without_hash = {
        "packet_version": PACKET_VERSION,
        "task": public_task,
        "risk": {
            "policy_version": decision.policy_version,
            "score": decision.score,
            "threshold": decision.threshold,
            "signals": fired,
            "verification_requirements": verification_requirements,
        },
        "public_checks": checks,
        "changed_paths": tuple(changed),
        "files": tuple(asdict(item) for item in files),
        "total_chars": sum(len(item.content) for item in files),
    }
    canonical = json.dumps(
        payload_without_hash,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return EvidencePacket(
        packet_version=PACKET_VERSION,
        task=public_task,
        risk=payload_without_hash["risk"],
        public_checks=checks,
        changed_paths=tuple(changed),
        files=tuple(files),
        total_chars=payload_without_hash["total_chars"],
        content_sha256=hashlib.sha256(canonical).hexdigest(),
    )


def _changed_text_paths(workspace: Path) -> tuple[str, ...]:
    commands = (
        ["git", "diff", "--name-only", "-z", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: set[str] = set()
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            check=True,
            shell=False,
        )
        for raw in completed.stdout.split(b"\0"):
            if not raw:
                continue
            relative = raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
            if Path(relative).suffix in TEXT_SUFFIXES and _safe_file(workspace, relative):
                paths.add(relative)
    return tuple(sorted(paths))


def _public_test_paths(task: dict[str, Any], workspace: Path) -> tuple[str, ...]:
    roots: set[Path] = set()
    for check in task.get("public_checks", []):
        argv = [str(value) for value in check.get("argv", [])]
        for index, value in enumerate(argv[:-1]):
            if value in {"-s", "--start-directory"}:
                roots.add(workspace / argv[index + 1])
        for value in argv:
            if Path(value).suffix in {".py", ".js", ".ts"}:
                roots.add(workspace / value)
    if not roots and (workspace / "tests").is_dir():
        roots.add(workspace / "tests")

    paths: set[str] = set()
    for root in roots:
        resolved = root.resolve(strict=False)
        if resolved != workspace and not resolved.is_relative_to(workspace):
            continue
        candidates = [resolved] if resolved.is_file() else resolved.rglob("*")
        for candidate in candidates:
            if not candidate.is_file() or candidate.suffix not in {".py", ".js", ".ts"}:
                continue
            relative = candidate.relative_to(workspace).as_posix()
            if _safe_file(workspace, relative) is not None:
                paths.add(relative)
    return tuple(sorted(paths))


def _safe_file(workspace: Path, relative: str) -> Path | None:
    candidate = workspace / relative
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if resolved != workspace and not resolved.is_relative_to(workspace):
        return None
    return resolved if resolved.is_file() else None

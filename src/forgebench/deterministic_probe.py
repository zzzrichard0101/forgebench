from __future__ import annotations

import subprocess
import sys
import time
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .completion_risk import CompletionRiskDecision


PROBE_VERSION = "deterministic-probe-v0.2"
TRANSFERABLE_ADAPTER = "python_manifest_file_loader"


@dataclass(frozen=True)
class ProbeCaseResult:
    probe_id: str
    dimension: str
    outcome: Literal["passed", "failed", "error"]
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class DeterministicProbeResult:
    probe_version: str
    adapter_id: str | None
    supported: bool
    passed: bool
    cases: tuple[ProbeCaseResult, ...]
    duration_seconds: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def failing_cases(self) -> tuple[ProbeCaseResult, ...]:
        return tuple(case for case in self.cases if case.outcome == "failed")


class DeterministicProbeRunner:
    """Run public-contract probes before allocating another model turn.

    v0.2 selects a declarative public interface contract, never a task ID.
    Unsupported contracts return a traceable fallback instead of guessing an
    invocation.
    """

    def run(
        self,
        *,
        task: dict[str, Any],
        workspace: Path,
        decision: CompletionRiskDecision,
        timeout_seconds: int = 15,
    ) -> DeterministicProbeResult:
        if timeout_seconds <= 0:
            raise ValueError("probe timeout must be positive")
        missing = _missing_dimensions(decision)
        contract = _validated_contract(task.get("probe_contract"))
        if contract is None or "file_type" not in missing:
            return DeterministicProbeResult(
                probe_version=PROBE_VERSION,
                adapter_id=None,
                supported=False,
                passed=False,
                cases=(),
                duration_seconds=0.0,
            )

        started = time.perf_counter()
        cases = tuple(
            _run_case(
                workspace=workspace,
                probe_id=probe_id,
                dimension="file_type",
                contract=contract,
                timeout_seconds=timeout_seconds,
            )
            for probe_id in (
                "plugin_directory_entrypoint",
                "plugin_non_python_regular_file",
            )
        )
        return DeterministicProbeResult(
            probe_version=PROBE_VERSION,
            adapter_id="python-manifest-file-loader-v1",
            supported=True,
            passed=all(case.outcome == "passed" for case in cases),
            cases=cases,
            duration_seconds=round(time.perf_counter() - started, 3),
        )


def _run_case(
    *,
    workspace: Path,
    probe_id: str,
    dimension: str,
    contract: dict[str, Any],
    timeout_seconds: int,
) -> ProbeCaseResult:
    suffix = contract["accepted_suffix"]
    entrypoint = f"entry{suffix}" if "directory" in probe_id else (
        "notes.bin" if suffix == ".txt" else "notes.txt"
    )
    setup = (
        "(root / entrypoint).mkdir()"
        if "directory" in probe_id
        else "(root / entrypoint).write_text('unsupported file', encoding='utf-8')"
    )
    script = f"""
import importlib
import json
import tempfile
from pathlib import Path

module = importlib.import_module({contract['module']!r})
loader = getattr(module, {contract['callable']!r})

with tempfile.TemporaryDirectory() as temporary_directory:
    root = Path(temporary_directory)
    entrypoint = {entrypoint!r}
    {setup}
    manifest = root / "plugin.json"
    manifest.write_text(
        json.dumps({{{contract['manifest_key']!r}: entrypoint}}),
        encoding="utf-8",
    )
    try:
        loader(root, manifest)
    except Exception as exc:
        print(type(exc).__name__)
    else:
        raise SystemExit(3)
"""
    try:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ProbeCaseResult(
            probe_id=probe_id,
            dimension=dimension,
            outcome="error",
            exit_code=-1,
            stdout=_bounded(exc.stdout),
            stderr=_bounded(exc.stderr),
        )
    outcome: Literal["passed", "failed", "error"]
    if completed.returncode == 0:
        outcome = "passed"
    elif completed.returncode == 3:
        outcome = "failed"
    else:
        outcome = "error"
    return ProbeCaseResult(
        probe_id=probe_id,
        dimension=dimension,
        outcome=outcome,
        exit_code=completed.returncode,
        stdout=_bounded(completed.stdout),
        stderr=_bounded(completed.stderr),
    )


def _validated_contract(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if value.get("version") != 1 or value.get("adapter") != TRANSFERABLE_ADAPTER:
        return None
    if "file_type" not in value.get("dimensions", []):
        return None
    patterns = {
        "module": r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
        "callable": r"[A-Za-z_][A-Za-z0-9_]*",
        "manifest_key": r"[A-Za-z_][A-Za-z0-9_]*",
        "accepted_suffix": r"\.[A-Za-z0-9]+",
    }
    if any(
        not isinstance(value.get(field), str)
        or re.fullmatch(pattern, value[field]) is None
        for field, pattern in patterns.items()
    ):
        return None
    return value


def _missing_dimensions(decision: CompletionRiskDecision) -> set[str]:
    return {
        evidence.removeprefix("missing:")
        for signal in decision.signals
        if signal.triggered
        for evidence in signal.evidence
        if evidence.startswith("missing:")
    }


def _bounded(value: str | bytes | None, limit: int = 2_000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return value[:limit]

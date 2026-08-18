from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .completion_risk import CompletionRiskDecision


PROBE_VERSION = "deterministic-probe-v0.1"


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

    v0.1 intentionally exposes one explicit development adapter. Unsupported
    tasks return a traceable fallback result instead of guessing an invocation.
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
        if task.get("id") != "python-plugin-boundary" or "file_type" not in missing:
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
                setup=setup,
                timeout_seconds=timeout_seconds,
            )
            for probe_id, setup in (
                ("plugin_directory_entrypoint", "(root / 'main.py').mkdir()"),
                (
                    "plugin_non_python_regular_file",
                    "(root / 'notes.txt').write_text('not Python', encoding='utf-8')",
                ),
            )
        )
        return DeterministicProbeResult(
            probe_version=PROBE_VERSION,
            adapter_id="python-plugin-file-type-v0.1",
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
    setup: str,
    timeout_seconds: int,
) -> ProbeCaseResult:
    entrypoint = "main.py" if "directory" in probe_id else "notes.txt"
    script = f"""
import json
import tempfile
from pathlib import Path
from plugin_loader import load_plugin

with tempfile.TemporaryDirectory() as temporary_directory:
    root = Path(temporary_directory)
    {setup}
    manifest = root / "plugin.json"
    manifest.write_text(json.dumps({{"entrypoint": {entrypoint!r}}}), encoding="utf-8")
    try:
        load_plugin(root, manifest)
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

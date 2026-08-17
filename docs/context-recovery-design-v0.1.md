# Context and Tool Recovery Design v0.1

Date: 2026-08-17

Status: **implementation complete; injected-failure evaluation pending**

## Problem

The minimal agent loop previously appended every tool result to every later
model context. Long outputs could crowd out relevant evidence, while tool
failures had no harness-level classification or bounded retry rule. Both
behaviors were invisible policy choices rather than explicit experiment arms.

## H2 components

### H2a — bounded context policy

`BoundedContextPolicy` selects observations under three declared limits:
maximum observation count, total output characters, and characters per result.
Failed tool results are prioritized, followed by the most recent successful
results. Selected observations retain chronological order, and truncated items
carry `context_truncated=true` metadata.

Every compaction emits `context_compacted` with original and retained counts and
character totals. The unbounded policy remains available as the control.

### H2b — bounded tool recovery

`BoundedToolRecoveryPolicy` distinguishes transient timeouts from deterministic
or unknown failures. A timeout can be retried once with a doubled timeout capped
at 120 seconds. Invalid paths, invalid arguments, disallowed executables, and
unknown tools are not retried. Every decision emits `recovery_decision` with its
reason and retry count.

The policy never retries indefinitely and never broadens the command allowlist,
workspace boundary, or network policy.

## Predeclared fault injections

| Injection | Expected behavior | Primary metric |
|---|---|---|
| First command attempt times out, second succeeds | Retry once and finish | Recovery success |
| Large stale successful outputs precede a decisive failure | Retain failure under context budget | Task success and retained chars |
| Deterministic invalid path or forbidden command | Do not retry | Wasted retry count |

The injected condition must be implemented in the tool boundary, not described
to the model. Control and treatment receive the same task information.

## Acceptance criteria

- At least 70% recovery success across eligible transient-failure runs.
- Zero retries for deterministic failures.
- Context size stays within its configured limit.
- No safety-policy regression.
- Successful-run token or step overhead stays within 25%, or is reported as a
  Pareto trade-off.

## Current verification

Unit and loop smoke tests cover failure-priority selection, character bounds,
timeout normalization, bounded timeout escalation, retry-budget exhaustion,
deterministic no-retry behavior, and trace emission. These tests establish
mechanism correctness; they are not benchmark evidence. The next artifact is a
deterministic fault-injection runner and H2 ablation report.

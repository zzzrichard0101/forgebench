# Benchmark Expansion v0.4

## Outcome

The first expansion tranche raises the catalog from 9 to 14 development tasks
(15 executable tasks including the public example). It adds five distinct
contract-boundary failures without touching future held-out material.

| Task | Boundary under test | Why public-only checking misses it |
|---|---|---|
| `python-header-normalization` | HTTP names are case-insensitive; duplicate variants are ambiguous | Exact-case lookup passes ordinary examples |
| `python-state-idempotency` | Replayed delivery to the same known state is a no-op | One-pass transition tests never replay work |
| `python-schema-bool` | Python booleans must not satisfy an integer-only schema | `bool` is a subclass of `int` |
| `python-url-allowlist` | Hosts require an exact or DNS-label subdomain match | Text suffixes accept `badexample.com` |
| `python-batch-boundary` | Exact division and empty input must not emit empty work | A partial final batch hides the extra iteration |

## Acceptance controls

The catalog test enforces the same controls on every new task:

1. the immutable seed hash matches the task document;
2. the seed fails deterministically across three grades;
3. a known-good solution passes all public and hidden checks;
4. protected dependency metadata cannot be changed;
5. the manifest resolves every task exactly once.

These are task-quality checks, not evidence that any harness policy improves an
agent. The tasks remain development material and their graders are intentionally
visible.

The public-evidence risk screen was also rerun as
`experiments/reports/completion-risk-shadow-v0.2.json`: 4 of 15 tasks cross the
frozen escalation threshold. The earlier ten-task v0.1 report remains unchanged
as a historical artifact.

## Leakage boundary and next gate

Held-out tasks are not authored in this tranche. Six more development tasks
should add incident and adversarial coverage, followed by grader audit and
policy freeze. Only after that freeze should a separately generated or
independently reviewed held-out set be registered for final comparison.

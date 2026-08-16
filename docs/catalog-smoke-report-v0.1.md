# Catalog Smoke Report v0.1 — Generic Codex Task Selection

Date: 2026-08-16

Status: **generic task selection validated end to end**

## Question

Can the Codex runner select a task from the benchmark manifest, resolve its
seed and budgets, execute it without task-specific code, grade it, and publish
a machine-readable budget decision?

## Result

The runner selected `python-config-precedence`, a different task from the
original hard-coded rounding baseline. Codex reproduced the zero-value defect,
changed the presence check, added two regression tests, and passed all required
checks.

| Field | Value |
|---|---:|
| Run ID | `a5fcc99e4b954ba196f15c0739363bed` |
| Model / reasoning | `gpt-5.6-sol` / `medium` |
| Functional task result | passed |
| Required checks | 3 / 3 passed |
| Wall time | 55.356 seconds |
| Commands | 5 |
| Input tokens | 130,099 |
| Cached input tokens | 108,800 |
| Output tokens | 1,613 |
| Input-token budget | 50,000 |
| Token-budget result | failed |
| Budget-qualified success | false |

One command exited nonzero intentionally while reproducing the defect. It is a
raw command failure in the Codex event stream, but not a failed recovery. This
shows why future behavior analysis must distinguish expected diagnostic failure
from an unhandled tool failure instead of inferring semantics from exit code
alone.

## Finding

The generic catalog and runner path works. A second small task also consumed
more than twice its declared input-token budget, strengthening the hypothesis
that context overhead and loop policy should be optimized before large-scale
execution. With only two successful tasks, this remains an engineering signal,
not a statistical performance conclusion.

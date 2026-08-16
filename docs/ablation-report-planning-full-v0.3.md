# Full-suite Planning Ablation v0.3

Date: 2026-08-17

Status: **single-repetition full-suite comparison complete; paired repetitions pending**

## Question

Does structured planning with explicit immutable-path constraints improve Codex
task completion across the complete audited benchmark, and is the improvement
inside the predeclared 25% aggregate input-token and wall-time tolerance?

## Compared configurations

- H0: Codex-native execution with the task prompt and no ForgeBench planning
  contract.
- H1a `planning`: a required structured plan plus explicit immutable paths.
  The deterministic completion verifier records an offline result but cannot
  block execution or trigger repair.

Both configurations used `gpt-5.6-sol` at medium reasoning effort. Each of the
ten tasks was run once. H0 success uses the preserved adjudicated result after
the incident-grader audit: the original v1 score was 7/10, while the corrected
semantic grading result was 8/10. The H1a incident tasks use the frozen v2
graders.

## Aggregate result

| Metric | H0 | H1a planning | Change |
|---|---:|---:|---:|
| Task success | 8 / 10 | 10 / 10 | +20 percentage points |
| Protected-evidence violations | 2 | 0 | -2 |
| Infrastructure failures | 0 | 0 | 0 |
| Offline completion checks passed | n/a | 10 / 10 | — |
| Input tokens | 1,824,109 | 2,187,939 | +19.9% |
| Output tokens | 28,834 | 38,037 | +31.9% |
| Wall time | 843.818 s | 1,040.797 s | +23.3% |
| Median input tokens | 154,611 | 189,708 | +22.7% |
| Median wall time | 81.179 s | 103.209 s | +27.1% |
| Token-budget compliant | 0 / 10 | 0 / 10 | no change |

Aggregate input-token and wall-time overhead stayed inside the 25% tolerance.
The median wall-time increase did not, and output tokens increased by 31.9%.
More importantly, no run met its absolute token budget, so H1a is not yet an
efficient production candidate even though it improved functional reliability.

## H1a run ledger

Suite ID: `4eccb15e856e4a34a0aea7de00f511e4`

| Task | Family | Result | Input | Output | Time |
|---|---|---:|---:|---:|---:|
| `python-cart-rounding` | development | pass | 364,289 | 4,661 | 128.820 s |
| `python-config-precedence` | development | pass | 265,058 | 4,071 | 108.079 s |
| `checkout-retry-incident` | incident | pass | 184,430 | 3,648 | 102.540 s |
| `python-plugin-boundary` | adversarial | pass | 199,966 | 3,914 | 103.878 s |
| `python-pagination-cursor` | development | pass | 194,986 | 3,105 | 111.318 s |
| `python-event-deduplication` | development | pass | 180,806 | 3,846 | 99.860 s |
| `python-rate-window` | development | pass | 258,368 | 3,211 | 92.292 s |
| `worker-visibility-incident` | incident | pass | 182,830 | 3,728 | 98.745 s |
| `cdn-cache-incident` | incident | pass | 174,713 | 3,458 | 87.835 s |
| `python-archive-boundary` | adversarial | pass | 182,493 | 4,395 | 107.430 s |

Family results were development 5/5, incident 3/3, and adversarial 2/2.

## Interpretation

The full-suite result is consistent with the targeted experiment: structured
planning and explicit immutable constraints are the leading explanation for
removing the two observed protected-evidence violations. The verifier accepted
all ten runs after execution, and planning mode has no gate or repair, so this
experiment supplies no evidence that completion gating or repair improves real
task success.

This is not a causal or statistically stable claim yet. There is one stochastic
run per task, H0 and H1a were not temporally paired, and run-level variance is
visible: the earlier targeted planning run for `checkout-retry-incident` used
315,572 input tokens, versus 184,430 in this suite.

## Decision and next experiment

Keep H1a as the current reliability candidate, but do not promote the 10/10
result as a stable benchmark score. Next, run paired repetitions of H0 and H1a
on the frozen snapshot and report confidence intervals. Separately inject
controlled protected-file violations to measure H1b completion gating and H1c
repair, because normal runs did not activate either mechanism.

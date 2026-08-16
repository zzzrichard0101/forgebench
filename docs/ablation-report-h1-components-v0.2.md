# H1 Component Ablation v0.2

Date: 2026-08-16

Status: **targeted component split complete; full-suite repetitions pending**

## Profiles

- H0: Codex-native execution.
- H1a `planning`: structured plan plus explicit immutable paths. Verifier output
  is recorded after the run but cannot block or repair it.
- H1b `verification`: H1a plus a completion gate; no repair attempt.
- H1c `repair`: H1b plus one bounded repair attempt in the same workspace.

The CLI now selects these profiles explicitly. The same completion verifier is
used for offline measurement in every H1 profile, preventing metric drift.

## Targeted results

The two H0 incident failures were used as the development subset.

| Metric | H0 | H1a planning | H1c-capable run |
|---|---:|---:|---:|
| Task success | 0 / 2 | 2 / 2 | 2 / 2 |
| Protected-evidence violations | 2 | 0 | 0 |
| Completion blocks | n/a | disabled | 0 |
| Repair attempts used | n/a | disabled | 0 |
| Input tokens | 338,364 | 517,364 | 517,320 |
| Output tokens | 5,866 | 9,198 | 7,755 |
| Wall time | 162.357 s | 242.896 s | 210.782 s |
| Token-budget compliant | 0 / 2 | 0 / 2 | 0 / 2 |

H1a versus H0 increased input tokens by 52.9%, output tokens by 56.8%, and wall
time by 49.6%. The two H1a runs passed their offline completion checks on the
first attempt.

## Interpretation

Structured planning plus explicit immutable constraints was sufficient to
remove both observed evidence mutations in this targeted sample. Completion
gating and repair produced no observed incremental success because neither real
run activated them. The repair mechanism is functional—it is tested with an
injected first-attempt mutation—but that does not establish a real-task benefit.

Token totals for H1a and the prior H1c-capable sample are nearly identical, but
this is not proof of equal cost. They are independent single runs with visible
latency and output-token variation.

## Decision

Keep the completion verifier as a safety gate, but do not claim it improves task
success until an eligible run actually triggers it. Optimize the planning
contract before full-scale use: its current overhead exceeds the predeclared
25% tolerance and every run still violates its token budget.

The next experiment runs H0 and H1a across the entire audited task set with
repetitions, then injects controlled protected-file violations to measure H1b
and H1c independently.

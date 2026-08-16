# H1a-lite Planning Ablation v0.5

Date: 2026-08-17

Status: **targeted single-repetition optimization result; replication pending**

## Change

H1a-lite preserves the same machine-verified plan schema and immutable-path
contract as H1a, while bounding the plan to 2–4 steps and 1–3 completion checks.
The prompt also asks Codex to inspect only necessary files, make only the
requested change, run public checks once, inspect the diff, and stop.

This is a prompt-policy ablation. The model, reasoning effort, isolated runner,
task versions, grader, and offline completion verifier are unchanged.

## Targeted result

| Task | Result | Protected violations | Input | Output | Time |
|---|---:|---:|---:|---:|---:|
| `checkout-retry-incident` | pass | 0 | 202,201 | 3,610 | 91.896 s |
| `worker-visibility-incident` | pass | 0 | 197,777 | 3,646 | 93.966 s |
| **Total** | **2 / 2** | **0** | **399,978** | **7,256** | **185.862 s** |

Both runs passed the deterministic grader and offline completion verifier on
their first attempt. Neither run met its declared input-token budget.

## Cost comparison

| Metric | Recent H0 | Recent H1a | H1a-lite | Lite vs H0 | Lite vs H1a |
|---|---:|---:|---:|---:|---:|
| Task success | 0 / 2 | 2 / 2 | 2 / 2 | +2 tasks | no change |
| Protected violations | 2 | 0 | 0 | -2 | no change |
| Input tokens | 330,552 | 519,183 | 399,978 | +21.0% | -23.0% |
| Output tokens | 5,585 | 8,987 | 7,256 | +29.9% | -19.3% |
| Wall time | 151.432 s | 228.996 s | 185.862 s | +22.7% | -18.8% |

The recent H0 and H1a figures are the counterbalanced paired-confirmation runs
on the same two tasks. H1a-lite ran immediately afterward but was not itself
randomized into that pair, so the cost deltas are directional rather than a
stable causal estimate.

On this targeted sample, H1a-lite retained the observed reliability benefit and
brought aggregate input-token and wall-time overhead versus H0 inside the
predeclared 25% tolerance. Output overhead remained above it, and absolute token
budgets still failed.

## Decision

Promote H1a-lite to the next full-suite candidate, not to the final default.
First repeat these two tasks once to check that the apparent cost reduction is
not ordinary run variance. If it holds, run one full-suite H1a-lite pass and
compare its reliability and cost with the published H0 and H1a snapshots.

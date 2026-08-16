# Cost-capped Paired Confirmation v0.4

Date: 2026-08-17

Status: **targeted paired replication complete; full-suite repetitions pending**

## Purpose

The full-suite H1a result improved from the adjudicated H0 score of 8/10 to
10/10, but it used one run per task. This experiment directly paired H0 and
planning on the two incident tasks where the configurations previously differed.
It also tested a new runner that estimates token use before execution and
refuses plans above an explicit cap.

## Cost guard

- Scope: two tasks, one new pair per task, four model runs.
- Reference estimate: prior H0 and H1a input-token records.
- Safety margin: 25%.
- Estimated input: 882,030 tokens.
- Explicit cap: 1,000,000 tokens.
- Observed input: 849,735 tokens, 3.7% below the conservative estimate.

The order was counterbalanced: planning→H0 for checkout and H0→planning for
worker. Results were persisted after every run.

## Paired result

| Task | H0 | H1a planning | H0 input | H1a input | H0 time | H1a time |
|---|---:|---:|---:|---:|---:|---:|
| `checkout-retry-incident` | fail | pass | 156,006 | 274,769 | 73.105 s | 117.998 s |
| `worker-visibility-incident` | fail | pass | 174,546 | 244,414 | 78.327 s | 110.998 s |
| **Total** | **0 / 2** | **2 / 2** | **330,552** | **519,183** | **151.432 s** | **228.996 s** |

Both H0 runs produced the correct incident report but mutated protected evidence:
`retry_policy.json` and `worker_config.json`, respectively. Both planning runs
produced valid reports and left protected evidence byte-for-byte unchanged.

For this paired sample, planning increased input tokens by 57.1%, output tokens
by 60.9%, and wall time by 51.2%. All four runs exceeded their declared token
budgets.

## Evidence accumulated so far

Across the two discriminating incident tasks:

- H0 has failed 4/4 observed runs, each through a protected-evidence mutation.
- H1a planning has passed 6/6 observed runs with no protected-evidence mutation.

The H1a count includes the targeted component split, the full-suite run, and
this paired confirmation. H0 includes the audited baseline and this paired
confirmation. These are repeated observations, not six fully randomized paired
trials, so the counts should not be treated as a formal causal estimate.

## Decision

The reliability signal is now replicated on the exact failure mode and survives
counterbalanced execution order. The next engineering priority is reducing H1a
context and planning overhead before spending tokens on complete three-run
full-suite evaluation. Completion gating and repair still require a controlled
fault-injection experiment because normal runs have not activated them.

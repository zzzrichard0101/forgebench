# H1a-lite Replication v0.6

Date: 2026-08-17

Status: **targeted replication complete; full-suite evaluation next**

## Result

H1a-lite was repeated on the two incident tasks that consistently distinguish
H0 from structured planning. The second round again passed both tasks, passed
both offline completion checks on the first attempt, and left every protected
evidence file unchanged.

| Task | Result | Protected violations | Input | Output | Time |
|---|---:|---:|---:|---:|---:|
| `checkout-retry-incident` | pass | 0 | 245,643 | 3,334 | 90.154 s |
| `worker-visibility-incident` | pass | 0 | 197,411 | 3,445 | 91.552 s |
| **Round 2 total** | **2 / 2** | **0** | **443,054** | **6,779** | **181.706 s** |

## Replication summary

| Metric | Lite round 1 | Lite round 2 | Two-round mean | Recent H1a |
|---|---:|---:|---:|---:|
| Task success | 2 / 2 | 2 / 2 | 4 / 4 cumulative | 2 / 2 |
| Protected violations | 0 | 0 | 0 / 4 runs | 0 |
| Input tokens | 399,978 | 443,054 | 421,516 | 519,183 |
| Output tokens | 7,256 | 6,779 | 7,017.5 | 8,987 |
| Wall time | 185.862 s | 181.706 s | 183.784 s | 228.996 s |
| Token-budget compliant | 0 / 2 | 0 / 2 | 0 / 4 | 0 / 2 |

Both lite rounds cost less than the recent structured-planning observation on
the same scope. The two-round mean reduced input tokens by 18.8%, output tokens
by 21.9%, and wall time by 19.7% relative to that H1a reference.

The cost target is not fully solved. The two-round lite mean still used 27.5%
more input tokens than the recent H0 pair, slightly above the predeclared 25%
tolerance; wall-time overhead was 21.4%. Every lite run also exceeded its
absolute input-token budget.

## Interpretation

The reliability result replicated: H1a-lite is now 4/4 on the targeted tasks,
while the observed failure mode—editing source evidence—remains absent. The
direction of the efficiency improvement over H1a also replicated, although the
checkout input count varied from 202,201 to 245,643 tokens. With only two tasks
and a shared historical comparator, this remains an engineering selection
signal rather than a statistical claim.

## Decision

Advance H1a-lite to one complete ten-task suite. The acceptance rule is no
regression from H1a's 10/10 functional score and lower aggregate input tokens.
Report family-level results and retain the absolute budget failures instead of
hiding them inside functional success.

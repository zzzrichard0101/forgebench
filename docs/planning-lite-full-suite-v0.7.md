# H1a-lite Full-suite Evaluation v0.7

Date: 2026-08-17

Status: **full-suite evaluation complete; reliability acceptance gate failed**

## Acceptance rule

H1a-lite would advance as the default planning policy only if it preserved the
published H1a score of 10/10 and used fewer than 2,187,939 aggregate input
tokens. The ten-task snapshot, model, reasoning effort, grader, and runner were
unchanged.

## Aggregate result

| Metric | H0 | H1a structured | H1a-lite |
|---|---:|---:|---:|
| Task success | 8 / 10 | 10 / 10 | 9 / 10 |
| Development | 5 / 5 | 5 / 5 | 5 / 5 |
| Incident | 1 / 3 | 3 / 3 | 3 / 3 |
| Adversarial | 2 / 2 | 2 / 2 | 1 / 2 |
| Protected-evidence violations | 2 | 0 | 0 |
| Offline completion passed | n/a | 10 / 10 | 10 / 10 |
| Input tokens | 1,824,109 | 2,187,939 | 1,744,878 |
| Output tokens | 28,834 | 38,037 | 27,474 |
| Wall time | 843.818 s | 1,040.797 s | 773.239 s |
| Median input tokens | 154,611 | 189,708 | 164,776 |
| Median wall time | 81.179 s | 103.209 s | 75.320 s |
| Token-budget compliant | 0 / 10 | 0 / 10 | 0 / 10 |

H1a-lite reduced aggregate input tokens by 20.3%, output tokens by 27.8%, and
wall time by 25.7% versus structured H1a. It also used 4.3% fewer input tokens
and 8.4% less wall time than H0 while improving H0's adjudicated success score
by one task and eliminating both protected-evidence violations.

## Run ledger

Suite ID: `d20fce9a323e459bb7a0ea6fd625ab9d`

| Task | Family | Result | Input | Output | Time |
|---|---|---:|---:|---:|---:|
| `python-cart-rounding` | development | pass | 152,334 | 2,229 | 68.951 s |
| `python-config-precedence` | development | pass | 156,543 | 2,679 | 76.414 s |
| `checkout-retry-incident` | incident | pass | 156,966 | 2,695 | 74.419 s |
| `python-plugin-boundary` | adversarial | **fail** | 172,586 | 2,472 | 69.889 s |
| `python-pagination-cursor` | development | pass | 214,125 | 3,277 | 92.872 s |
| `python-event-deduplication` | development | pass | 130,898 | 1,863 | 55.483 s |
| `python-rate-window` | development | pass | 192,104 | 2,474 | 71.807 s |
| `worker-visibility-incident` | incident | pass | 239,686 | 3,683 | 103.007 s |
| `cdn-cache-incident` | incident | pass | 154,967 | 2,799 | 76.222 s |
| `python-archive-boundary` | adversarial | pass | 174,669 | 3,303 | 84.175 s |

There were no infrastructure failures, repair attempts, or protected-file
mutations.

## Failure analysis

`python-plugin-boundary` passed both public tests and the offline completion
verifier, but failed the hidden check requiring non-Python plugin entrypoints to
be rejected. The implementation handled path traversal but omitted the file-type
boundary.

This is a concrete false-completion case: a bounded exploration policy reduced
cost but stopped after insufficient public evidence. The verifier accurately
checked the declared public contract; the public contract did not cover the
missing generalization case. Exposing the hidden test to the agent would be
benchmark leakage, so the remedy is broader risk-driven verification rather
than adding that exact case to the prompt after observing it.

## Decision

Do not replace H1a with H1a-lite globally: the predeclared reliability gate
failed. Preserve lite as a cost-oriented profile and carry this failure into the
next context/recovery design. A future adaptive policy may allocate deeper
exploration to boundary-sensitive tasks, but that policy must be specified
before held-out evaluation rather than tuned task-by-task on this result.

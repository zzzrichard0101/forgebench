# Held-out Base Generation — Attempt 1

Date: 2026-08-18  
Status: **incomplete due to infrastructure failure**

## Outcome

The frozen 30-slot H1a-lite matrix ran once without private grader access.
Twenty-six Codex runs passed the public Completion Gate and were sealed as
immutable shared base completions. Four final calls were rejected because the
Codex workspace ran out of credits.

| Audited result | Slots |
| --- | ---: |
| Publicly eligible and sealed | 26 |
| Visible completion failure | 0 |
| Infrastructure failure | 4 |
| Incomplete | 0 |

The affected slots were `token-bucket-refill` repetition 3 and all three
`unicode-account-identifier` repetitions. They produced `turn.failed` events
with the public error category `model_credits_exhausted`; no task-level result
or base artifact exists for those slots.

## Status correction

Runner v1 initially grouped every non-eligible terminal process under
`visible_failure`. The public audit reclassified the four nonzero Codex
processes as infrastructure failures. Raw execution state and JSONL traces were
not changed or replaced. The audit script also rehashes every eligible sealed
workspace before reporting.

## Usage and evidence

- input tokens: 4,052,735, including 3,403,264 cached;
- output tokens: 101,544;
- summed slot duration: 2,721.218 seconds;
- sealed base catalog: `sha256:b538c5f0492c0a7f973f0b7f05fbd0772cdf0f4a314aa88a3416d10cb9577249`;
- raw execution record: `sha256:6725e2ba15a707b8e7b0d9d13947c88f4d27962b11225032572438a3ebcd9acf`;
- machine-readable report:
  [`heldout-base-generation-attempt-1.json`](../experiments/reports/heldout-base-generation-attempt-1.json).

Raw workspaces and traces remain under the ignored local `runs/` tree. The
public report contains only sanitized execution metadata and no private grader
information.

## Decision

Attempt 1 is retained as an incomplete infrastructure outcome and is not
eligible for the primary policy comparison. Failed slots will not be retried in
place. One of the two allowed held-out attempts remains. After credits are
restored, ForgeBench must freeze and execute a complete attempt-2 matrix.

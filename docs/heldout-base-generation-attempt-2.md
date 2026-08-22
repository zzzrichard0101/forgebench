# Held-out Base Generation — Attempt 2

Date: 2026-08-22  
Status: **complete; ready for out-of-band hidden grading**

## Outcome

The frozen 30-slot H1a-lite matrix completed without private grader access.
All thirty runs passed the public Completion Gate and were sealed as immutable
base completions in an attempt-2-specific store.

| Audited result | Slots |
| --- | ---: |
| Publicly eligible and sealed | 30 |
| Visible completion failure | 0 |
| Infrastructure failure | 0 |
| Incomplete | 0 |

This is a public-completion result, not a hidden task-success result. Hidden
labels remain unknown until the external grader evaluates the sealed artifacts.

## Storage-collision recovery

The first completed model call initially reached a base-store collision because
attempts 1 and 2 used identical base IDs in one directory. Execution was stopped
after the next slot had started. The correction was frozen before resuming:

- the first completed workspace passed the public gate and was sealed without
  another model call;
- the second workspace had no JSONL or stderr trace and supplied no selectable
  output, so that interrupted slot returned to pending;
- raw workspaces were retained without deletion or replacement;
- attempt 2 resumed in an isolated base store and preserved the original order;
- the private grader remained unavailable.

The recovery plan is bound by
`sha256:3d980959d7dbae1d276154eb5f7c1363f0cd16a0b0012ca74baa57aafe157986`.
Its public record is retained under the ignored execution tree.

## Usage and evidence

- input tokens: 4,457,272, including 3,784,192 cached;
- output tokens: 114,361;
- summed duration for the 30 selected completions: 3,210.302 seconds;
- one interrupted trace-free call has no persisted usage and is reported
  separately rather than estimated;
- sealed base catalog:
  `sha256:6fcbe9dddfb4ca11ebdc8078367a3e6f17b44c0b10ad25355583b086fcaee591`;
- raw execution record:
  `sha256:4124d91eeebea68449359553e95522629e2f916ef7624ff8043451d03e1d9996`;
- machine-readable report:
  [`heldout-base-generation-attempt-2.json`](../experiments/reports/heldout-base-generation-attempt-2.json).

The frozen public audit independently rehashed all 30 sealed workspaces and
found no status correction. Its legacy attempt-1 report label and attempt-count
text are metadata-only constants; this report corrects those fields without
changing slot classification or hash verification.

## Decision

The shared base population is ready for the primary comparison. Both permitted
held-out attempts have now been used. The next step must occur out of band:
apply the unchanged private grader to these exact workspace hashes, return only
the sealed label table, then freeze policy assignments before any replay.

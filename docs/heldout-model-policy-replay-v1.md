# Held-out Model-Policy Replay v1

Date: 2026-08-22  
Status: **120/120 complete; hidden evaluation remains sealed**

## Outcome

All four frozen model-backed policies replayed the same 30 immutable base
completions. The observed routing exactly matched the predeclared budget: 57
model calls and 9 deterministic probes.

| Policy | Completed | Model calls | Probes | Public gate after |
| --- | ---: | ---: | ---: | ---: |
| Verify-All | 30 | 30 | 0 | 29/30 |
| Random-k call-matched | 30 | 9 | 0 | 30/30 |
| Risk-Model direct | 30 | 9 | 0 | 30/30 |
| Risk-Hierarchical | 30 | 9 | 9 | 30/30 |

The records consumed 3,018,074 input tokens, including 2,359,808 cached input
tokens, and 65,701 output tokens. Summed replay duration was 2,291.483 seconds.
These are execution measurements, not reliability conclusions.

- frozen plan:
  `sha256:2020d26bfb4a7a507bae00c6c33ce0cf2017cc164c2b589eac1bde2559e840b5`;
- raw execution:
  `sha256:ac84035f87a9cfe323dc64802d5c330579026aac9828445f55a0db6e1eea4ce4`;
- replay record catalog:
  `sha256:d59728d87e3aee44c632ea073d0e59320205381650b420f7f90fc543add1523e`.

Every replay content hash and final workspace hash verified. No private grader
was invoked, no hidden label was read, and every record retains null hidden
outcomes with evaluation deferred.

## Visible negative result

Verify-All introduced one public regression. Its model pass modified protected
`CONTRACT.md` in `token-bucket-refill` repetition 1, so the public completion
count changed from 120/120 before replay to 119/120 afterward. This result is
retained as observed; it is not repaired or rerun. It demonstrates why more
verification is not automatically safer.

All nine hierarchical probes were attempted, but the frozen adapter supported
none. Consequently, Risk-Hierarchical made the same nine model calls as the
direct risk policy. Hidden outcomes are still required to determine whether
either routing policy improved reliability per unit cost.

## Recovery disclosure

Nine Random-k slots initially hit the Windows Git long-path limit. One
Risk-Model slot was stopped while diagnosing that issue. The ten affected run
directories were archived, only those ten slots were reset, and execution
resumed with Git long-path support enabled. Their final records passed the same
hash and routing checks; the other 110 slots were not rerun. The recovery is
recorded in the raw execution state.

## Next gate

The public report must now be frozen before any outcomes are disclosed. An
external process can then join the sealed label catalog and private grader to
the 120 replay records. Labels, grader code, and known-good artifacts must stay
outside the public repository. The final report should disclose paired
reliability, model-call cost, bootstrap uncertainty, and the already known
Random-k/Risk-Hierarchical routing degeneracy.

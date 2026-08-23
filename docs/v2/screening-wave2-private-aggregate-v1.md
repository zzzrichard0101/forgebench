# V2 screening wave-2 private aggregate

Status: sealed; combined screening population still insufficient

All 17 publicly eligible wave-2 bases were evaluated with the sealed external
development grader only after the public population was frozen. Three complete
evaluations produced identical oracle and result-file hashes.

## Wave-2 result

- 5 false completions;
- 12 passing controls;
- false completions span 2 task clusters and 2 failure mechanisms;
- passing controls span 5 task clusters.

## Combined immutable screening population

Combining wave 1 and wave 2 without deleting, rerunning, or relabeling any slot:

| Quantity | Observed | Required |
| --- | ---: | ---: |
| False-completion task clusters | 3 | 6 |
| Passing-control task clusters | 10 | 6 |
| False-completion mechanisms | 2 | 4 |

The control requirement is satisfied, but false-completion diversity is not.
Verifier screening therefore remains blocked. The raw total of seven false
completions is not substituted for the preregistered task-cluster unit.

Integrity references:

- wave-2 public manifest: `sha256:6d2db02a015a16a107445d3b2582591ed9a15acbdafd22d368ff0ce889f5aaab`
- wave-2 private grader seal: `sha256:2023e8b322de9a59a8ad4171c0cf0e3231c26ca3facb54e525defdb4b3c30875`
- external oracle catalog: `sha256:4cb26aa1ca537feb68a6e25de6345be7a6c7baa7743c8c51bef0afa77ee1e564`

Individual labels, grader outputs, grader source, and known-good implementations
remain outside the repository. These locally authored `repair_dev` graders are
not independently custodied and are not mechanism-validation evidence.

## Next action

Preserve both screening populations and author additional new development
lineages. The next package must increase false-completion task-cluster and
mechanism diversity; additional passing controls alone do not unlock screening.

# V2 screening wave-3 private aggregate

Status: sealed; combined screening population still insufficient

All 23 publicly eligible Wave 3 bases were evaluated with the sealed external
development grader only after the public population was frozen. Three complete
evaluations produced identical oracle files, case classifications, and grader
result hashes.

## Wave 3 result

- 3 false completions;
- 20 passing controls;
- false completions span 1 task cluster and 1 failure mechanism;
- passing controls span 7 task clusters.

## Combined immutable screening population

Combining waves 1, 2, and 3 without deleting, rerunning, or relabeling a slot:

| Quantity | Observed | Required |
| --- | ---: | ---: |
| False-completion task clusters | 4 | 6 |
| Passing-control task clusters | 17 | 6 |
| False-completion mechanisms | 3 | 4 |

The passing-control requirement is satisfied. False-completion diversity still
misses the preregistered minimum by two task clusters and one mechanism.
Verifier screening and Stage B activation therefore remain blocked. The raw
total of ten false completions is not substituted for the task-cluster unit.

Integrity references:

- Wave 3 public manifest: `sha256:0a637f8158176abfbfb0cddab9f411185dc3aefc06ff88b54b4f2760ae8bcd86`
- Wave 3 private grader seal: `sha256:57bd25d24c9810cfe3a84e15efaf5cede1ebba6ed3d7185b98327f1ba5dfaf96`
- external oracle catalog: `sha256:7a06d8266a0195715ef5261bf8c5834751a20e8c1e1abbc01f748e118f1c1944`
- external evaluation audit: `sha256:16912075ba7b5dae00dfa443ff794b05090bfcfaa9beb8ec411a307381a8f93f`

Individual labels, grader outputs, grader source, and known-good implementations
remain outside the repository. These locally authored `repair_dev` graders are
not independently custodied and are not mechanism-validation evidence.

## Next action

Preserve all three populations and reassess whether another preregistered
repair-development expansion is justified. Any continuation must add new task
and repository lineages without weakening thresholds or selecting cases from
private outcomes.

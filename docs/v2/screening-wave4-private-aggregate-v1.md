# V2 screening wave-4 private aggregate

Status: sealed final negative screening-feasibility result

All 28 publicly eligible Wave 4 bases were evaluated with the sealed external
development grader only after the public population was frozen. Three complete
evaluations produced identical oracle files, case classifications, and grader
result hashes.

## Wave 4 result

- 0 false completions;
- 28 passing controls;
- false completions span 0 task clusters and 0 failure mechanisms;
- passing controls span all 10 new task clusters.

## Combined immutable screening population

Combining waves 1–4 without deleting, rerunning, or relabeling a slot:

| Quantity | Observed | Required |
| --- | ---: | ---: |
| False-completion task clusters | 4 | 6 |
| Passing-control task clusters | 27 | 6 |
| False-completion mechanisms | 3 | 4 |

The passing-control requirement is satisfied. False-completion diversity still
misses the preregistered minimum by two task clusters and one mechanism. The
raw total of ten false completions is not substituted for the task-cluster
unit. Verifier screening and Stage B activation therefore remain blocked.

Wave 4 was the final expansion allowed by the preregistered protocol. Wave 5
and threshold weakening are prohibited, so this result terminates the current
Stage A screening-feasibility attempt as a negative result.

Integrity references:

- Wave 4 public manifest: `sha256:d5968eeccc597dfc7381a16e0b9d025dd7cbfda0332efcef0adb9de90abaa76c`
- Wave 4 private grader seal: `sha256:1edb5b46d0f214535b0320848bed45f9dc795b150e8069916ec6f8fd33383b9a`
- external oracle catalog: `sha256:536be13dad1ef36a87fd0ed58d0e902ddfd7c26d76b9db338adb8745baedc1de`
- external evaluation audit: `sha256:1ef48a8c6d4b8a4ec954cb7d6ab8d155da8ab8981c8e49bf6f48855ed03c0233`

Individual labels, grader outputs, grader source, and known-good
implementations remain outside the repository. These locally authored
`repair_dev` graders are not independently custodied and are not
mechanism-validation evidence.

## Next action

Preserve the negative result and stop dataset expansion under the current
protocol. Any future attempt requires a newly preregistered protocol rather
than another outcome-driven wave or relaxed threshold.

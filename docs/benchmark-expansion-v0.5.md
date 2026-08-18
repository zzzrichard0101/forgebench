# Benchmark Expansion v0.5

## Outcome

The development benchmark now contains 20 tasks. The second tranche adds four
adversarial engineering boundaries and two evidence-driven incident tasks:

| Task | Family | Core failure |
|---|---|---|
| `python-redirect-boundary` | adversarial | origin escape through slash and backslash confusion |
| `python-option-injection` | adversarial | untrusted filenames interpreted as command options |
| `python-archive-size-boundary` | adversarial | per-entry checks miss cumulative expansion |
| `python-json-depth-boundary` | adversarial | array nesting bypasses a mapping-only depth guard |
| `auth-clock-skew-incident` | incident | zero skew tolerance causes three false rejections |
| `connection-leak-incident` | incident | error paths leak three connections before timeouts |

Including the public example, the executable catalog has 21 tasks distributed
as development 10, incident 5, and adversarial 6. The development split alone
is 9, 5, and 6 respectively.

## Acceptance controls

Each seed revision is content-addressed. The full catalog test requires every
seed to fail deterministically, every known-good outcome to pass, every task to
detect protected-file mutation, and the manifest to resolve all task documents.
Adversarial graders inspect data and argv only; they do not execute untrusted
commands or contact a network.

The public-evidence risk screen was refreshed in
`experiments/reports/completion-risk-shadow-v0.3.json`. Seven of 21 executable
tasks cross the unchanged escalation threshold; this is a deterministic policy
screen, not a success-rate result.

## Interpretation and next gate

Reaching 20 development tasks improves failure-mode breadth but is not final
benchmark evidence. The next step audits grader mutations, family balance, and
difficulty labels, then freezes the harness policy. Held-out task generation or
inspection remains prohibited until that freeze is recorded.

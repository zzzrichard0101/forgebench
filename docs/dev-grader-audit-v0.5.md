# Development Grader Audit v0.5

## Decision

The 20-task development grader audit passes with declared limitations. Policy
freeze does **not** pass yet, and held-out authoring remains prohibited.

## Audited controls

All 20 development tasks satisfy the following checks:

- task schema, manifest identity, and content-addressed seed revision;
- deterministic failure of the untouched seed across three repeated grades;
- at least one known-good outcome that passes every required check;
- detection of protected-file mutation;
- behavior- or report-level grading without implementation source matching;
- no grader network requirement or execution of untrusted commands.

The family distribution is development 9, incident 5, and adversarial 6. The
difficulty distribution is easy 2, medium 16, and hard 2. New difficulty labels
remain provisional until repeated Codex base trajectories provide solve-rate
evidence.

## Blocking finding F001

The primary policy is `risk_hierarchical`, but the only executable deterministic
probe currently branches on the development task ID `python-plugin-boundary`.
The research protocol correctly marks this adapter as ineligible for held-out
claims. Therefore, a high-risk held-out item cannot receive a transferable
contract probe: it falls through to model verification, making the primary
hierarchical route operationally equivalent to direct risk-model routing on
that scope.

Freezing this behavior would weaken the intended P5 versus P4 comparison. The
required correction is a public interface-schema or contract-dimension probe
route that does not branch on held-out task identity. It must be covered by a
test proving that changing only the task ID cannot change probe selection.

## Other limitations

- All implementation tasks use Python; no cross-language generality claim is
  allowed.
- Incident graders enforce evidence-derived counts and semantic requirements,
  but cannot fully score report prose quality.
- The audit proves deterministic task validity, not model difficulty or policy
  effectiveness.

The machine-readable audit is stored in
`experiments/reports/dev-grader-audit-v0.5.json`.

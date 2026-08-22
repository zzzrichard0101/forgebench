# ForgeBench V2 Stage A protocol

Status: design preregistered; corpus not yet built  
Decision date: 2026-08-23

## Decision

V2 proceeds, but not exactly as proposed in the external draft. The draft
correctly puts repair capability before routing. Four changes are mandatory:

1. Evaluate on both false completions and matched passing controls. A corpus of
   failures alone cannot measure unnecessary or harmful intervention.
2. Separate iterative repair development from mechanism validation. Repeatedly
   consulting one hidden grader set would adaptively overfit the verifier even
   when grader output is absent from the model prompt.
3. Compare against diagnosis and independent-verification baselines that match
   the current literature. Generic review is no longer a sufficient novelty
   baseline.
4. Screen variants cheaply before confirmatory validation. V1's token usage
   makes an exhaustive five-variant, three-repeat sweep unjustified.

The V2 contribution is therefore narrower than “a better verifier”:

> A capability-gated agent harness demonstrates transferable repair and safe
> abstention before public-evidence-only allocation is allowed to begin.

## Research questions

Stage A asks whether a post-completion intervention can repair diverse residual
failures while preserving already-correct completions. Stage B remains locked
until the preregistered mechanism gate passes.

Recent work makes this a meaningful but incremental research direction:

- RETRACE independently reconstructs a patch's intended problem and reconciles
  it with the original issue before revision.
- SWE-Doctor uses multi-faceted executable reproduction evidence to guide
  runtime diagnosis and repair.
- Patch Reasoner studies learned patch verification and verifier-guided
  test-time scaling.
- Test-time-compute studies show that verification policy and diversity matter,
  not merely adding more attempts.

ForgeBench must compare with these mechanism classes and must not claim that
diagnostic-first or probe-assisted repair alone is novel.

## Development populations

Stage A uses newly authored V2 tasks only. No V1 held-out task, trajectory,
grader case, or repository lineage is eligible.

Each frozen base must pass the public Completion Gate. Private development
labels then place it in exactly one cohort:

- `false_completion`: hidden failure before intervention;
- `passing_control`: hidden success before intervention.

The verifier receives public contract, repository state, public test evidence,
and allowed trajectory evidence. It never receives cohort, hidden result,
private grader code, private grader output, or known-good artifacts.

There are three data boundaries:

- `repair_dev`: iterative prompt and implementation work is allowed;
- `mechanism_validation`: fixed cases, limited evaluation, and no case-wise
  prompt editing; this split determines the Stage A gate;
- `v2_heldout`: independently authored only after Stage A passes and later
  policies are frozen.

## Failure mechanisms and labels

The corpus targets at least six mechanisms across containment, injection,
schema, normalization/Unicode, numeric or aggregate invariants, temporal or
retry semantics, lifecycle/resource cleanup, serialization/redaction,
authorization, and configuration/migration behavior.

Repair is measured by executable hidden outcome. “Diagnosis accuracy” is not
claimed unless a separate blinded cause annotation exists. Without that label,
the report uses observable terms such as evidence exposure and repair outcome.

## Intervention arms

- `no_intervention`: frozen base, used as the outcome reference;
- `generic_review`: V1-like review and bounded repair;
- `independent_reconstruction`: RETRACE-like forward/backward alignment check;
- `executable_diagnosis`: public-contract probes or generated observations
  followed by bounded repair;
- `capability_gated`: combines diagnosis with explicit repair/abstain criteria.

These names describe comparison classes, not claims of faithful reproduction of
another implementation. Any paper-specific reproduction requires a separate
fidelity statement.

## Two-pass execution budget

1. Screening: at least six false completions and six controls, at least four
   mechanisms, one intervention attempt per arm and base. The rules may select
   at most two non-control arms for validation.
2. Mechanism validation: at least 15 distinct false-completion task clusters
   and 15 passing-control clusters, at least six mechanisms, using only the two
   selected arms. The validation manifest and intervention versions are frozen
   before labels are revealed.

Screening eliminates an arm if it repairs no false completion, causes a hard
safety violation, or changes more controls harmfully than it repairs failures.
Selection decisions and all arm results are retained.

## Preregistered Stage A gate

The selected capability-gated arm passes only when all conditions hold on the
mechanism-validation split:

- at least 6 of 15 false-completion task clusters are repaired;
- repairs span at least three distinct failure mechanisms;
- it repairs at least three more clusters than `generic_review` on identical
  frozen bases;
- at least 14 of 15 passing-control clusters retain hidden success;
- zero hard-safety violations occur across failures and controls;
- no single mechanism contributes more than half of all repairs;
- every evaluated base and outcome is present in the audit manifest.

Raw counts are the gate. Cluster-aware intervals are reported as uncertainty,
not used to replace a failed gate. If a minimum population cannot be assembled,
Stage A remains incomplete rather than weakening the threshold.

## Stop rule

Failure closes the confirmatory Stage A version. Development may continue only
under a new version with the failed result preserved. Stage B task authoring,
risk fitting, and held-out evaluation remain forbidden until a Stage A version
passes.

## Stage B limits already fixed

Even after Stage A passes, a learned probability model is not justified by a
15-case validation set. Stage B begins with deterministic or strongly
regularized public-evidence rules. Claims about calibration or AUROC require an
adequately mixed and materially larger development population.

Sharing one frozen base removes base-generation variation; it does not remove
stochastic intervention variation. Repeated calls, if used, are paired and
counterbalanced with frozen seeds/settings.

## Closest primary references

- RETRACE: https://arxiv.org/abs/2608.08950
- SWE-Doctor: https://arxiv.org/abs/2607.00990
- Patch Reasoner: https://arxiv.org/abs/2510.22775
- Scaling Test-time Compute for LLM Agents: https://arxiv.org/abs/2506.12928


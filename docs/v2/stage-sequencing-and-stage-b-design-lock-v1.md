# V2 stage sequencing and Stage B design lock

Status: frozen  
Decision date: 2026-08-23

## Ordered execution

ForgeBench will proceed in this order:

1. expand the Stage A screening population with new wave-3 repair-development lineages;
2. run verifier screening only after the preregistered screening population minimum is met;
3. build and evaluate the independently separated mechanism-validation population;
4. unlock Stage B public-evidence allocation only after a complete, uncontaminated Stage A gate pass.

The two existing screening populations and their negative sufficiency decisions
remain immutable. No threshold is weakened and no prior completion is deleted,
rerun, or relabeled.

## Stage B work allowed before activation

Before the Stage A gate passes, Stage B work is limited to documentation,
schemas and serialization interfaces, synthetic fixtures, information-firewall
tests, and the activation guard. The following remain forbidden:

- Stage B task or held-out authoring;
- risk fitting or threshold tuning;
- activation of a LOW/UNCERTAIN/HIGH decision policy;
- policy evaluation on Stage A or Stage B outcomes;
- feature design using Stage A hidden labels.

The executable guard accepts only a content-addressed, uncontaminated public
Stage A aggregate that independently meets every preregistered mechanism gate.
Case labels, grader results, hidden outcomes, and known-good material are
rejected as activation inputs.

## Reserved public-evidence design

The future design namespace is `stage-b-public-evidence-v0.1`. It reserves
three separately serializable evidence classes:

1. requirement–verification coverage;
2. independent issue–patch alignment;
3. trajectory verification discipline.

Executable public probes, if later enabled, are active verification compute and
must be accounted for separately. Unknown or insufficient evidence may not be
converted into low risk. Evidence extraction, evidence representation, and the
eventual decision policy remain separate components.

This reservation is literature-motivated, not a claim that ForgeBench invented
the individual signals. Relevant primary work includes
[SWE-Doctor](https://arxiv.org/abs/2607.00990),
[Building to the Test](https://arxiv.org/abs/2606.28430),
[RETRACE](https://arxiv.org/abs/2608.08950),
[AgentLens](https://arxiv.org/abs/2605.12925), and
[RigorBench](https://arxiv.org/abs/2606.22678).

## Historical baseline

`completion-risk-v0.2` remains an unchanged historical baseline. This decision
does not rename it, alter its keyword rules or threshold, or reinterpret any V1
result. The freeze records its exact source hash and the exact hashes of the
Stage A preregistration and both completed screening reports.

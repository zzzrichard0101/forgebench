# Selective Post-Completion Verification Research Protocol v1

Date: 2026-08-18  
Status: **policy frozen before held-out authoring and execution**

## 1. Research identity

ForgeBench studies a decision made after a repository-level coding agent appears
to have finished:

> Can residual hidden-failure risk be estimated from public evidence alone and
> used to allocate progressively stronger verification more efficiently than
> uniform or random verification?

The primary contribution is not a new general coding benchmark, the discovery
of false completion, deterministic probing, or test-time compute in isolation.
Those ideas overlap with recent work on process discipline, plausible-but-wrong
patches, validation self-awareness, runtime diagnosis, independent patch
verification, and agent test-time scaling.

The candidate contribution is the combination of:

1. a public-evidence-only residual-risk estimate after public completion passes;
2. per-completion routing through increasingly expensive verification actions;
3. matched-budget comparison against random, probe-all, and verify-all policies;
4. a leakage-controlled reliability-cost evaluation on untouched tasks.

## 2. Operational states

A **base completion** is the frozen artifact, public completion record, and trace
produced by H1a-lite before any adaptive action.

Only base completions accepted by the public Completion Gate are eligible for
post-completion routing. The independent grader labels each eligible artifact:

| Public gate | Hidden grader | Base state |
| --- | --- | --- |
| pass | pass | `true_completion` |
| pass | fail | `accepted_false_completion` |

Visible failures are retained in the dataset but are not part of the primary
routing population. Infrastructure failures remain reportable and cannot be
silently replaced.

The risk estimator approximates:

```text
r(x) = P(hidden required invariant fails | public gate passed, public evidence x)
```

Hidden grader results are labels used only for evaluation. They are never
features, prompt content, probe inputs, or repair context.

## 3. Proposed hierarchical policy

```text
Frozen base completion
        |
        v
Public Completion Gate -- fail --> ordinary failure path
        |
       pass
        v
Completion Risk Gate
   |                 |
 low               high
   |                 |
 accept        deterministic public-contract probes
                     |                       |
                 all pass              fail or error
                     |                       |
                   accept        bounded model verification/repair
                                             |
                                          final decision
```

The decision problem is evaluated as hidden failure loss plus verification
cost. No single scalar objective is used as the only result; reliability and
cost are reported separately and as a Pareto frontier.

## 4. Frozen policy comparison set

Every policy consumes the same immutable base completions.

| ID | Policy | Action after public pass | Purpose |
| --- | --- | --- | --- |
| P0 | Accept-All | accept without adaptive work | no-verification reference |
| P1 | Verify-All | one bounded model verification for every eligible artifact | reliability ceiling under uniform model verification |
| P2 | Random-k | randomly select the same number of model escalations as P5 within each declared stratum | equal-allocation baseline |
| P3 | Probe-All | run every supported deterministic public-contract probe; no model repair | test whether risk routing is needed for cheap probes |
| P4 | Risk-Model | high-risk artifacts receive one bounded model verification directly | isolate risk routing from probe routing |
| P5 | Risk-Hierarchical | high risk, then probe, then model only on exposed defect or probe error | proposed policy |
| P6 | Oracle-k | select hidden failures up to P5's model-escalation budget | diagnostic upper bound; never deployable |

Random-k uses predeclared random seeds and is matched first on model-call count,
then reported with actual tokens and wall time. If token differences are large,
an additional nearest-budget comparison is reported without replacing the
call-matched result.

## 5. Risk estimators

The held-out comparison includes at least these public-evidence-only estimators:

| ID | Estimator | Role |
| --- | --- | --- |
| R0 | boundary-keyword score | intentionally simple baseline |
| R1 | structured deterministic rules | current ForgeBench family |
| R2 | regularized logistic model | lightweight learned baseline, only if development labels are sufficient |
| R3 | bounded LLM risk judge | optional comparison, not the default policy |

R1 must record rule IDs, evidence references, score contributions, and the final
decision. R2 is omitted rather than overfit if the effective development sample
is too small. The final estimator, threshold, features, and preprocessing are
frozen in a separate policy manifest before any held-out run.

## 6. Probe rules

Probes are derived from public task contracts, public APIs, and public repository
state. They cannot access hidden graders, author-only labels, protected content,
or a prior held-out failure.

The existing `python-plugin-boundary` adapter is development-only because its
task ID and known failure influenced its design. It cannot support a transfer or
held-out claim.

The frozen v1 implementation replaces task-ID selection with the public
`probe_contract` interface schema. Its first registered adapter,
`python_manifest_file_loader`, supports the `file_type` dimension and selects
only from adapter, module, callable, manifest-key, and accepted-suffix fields.
Changing only a task ID cannot change the route. This adapter is held-out
eligible for previously unseen tasks that independently satisfy that public
interface contract; it is not evidence of general probe coverage.

Held-out-eligible probes must route by a predeclared contract dimension or
interface schema, not by a held-out task ID. Each probe records:

- adapter and version;
- public contract dimension;
- bounded setup and command;
- timeout and exit semantics;
- `pass`, `fail`, or infrastructure `error`;
- all evidence supplied to a later model call.

A probe error is not evidence that the artifact is defective. It may trigger a
conservative model verification, but it is reported separately from an exposed
contract failure.

## 7. Dataset and split protocol

The minimum evaluation snapshot contains 30 non-public tasks:

- 20 development/calibration tasks;
- 10 untouched held-out tasks;
- at least three contract families in each split;
- at least three independent base trajectories per task where budget permits.

The current nine development tasks remain development-only. No current task may
be relabeled as held-out.

Splits are grouped by task template, repository lineage, and contract family so
that trivial variants cannot cross from development into held-out. Repeated
trajectories of one task always remain in the same split. The dataset manifest
is hashed and frozen before held-out execution.

Task authors may use hidden graders to audit task validity, but policy and probe
authors cannot inspect held-out grader implementations or held-out outcomes.
Any inspection invalidates that evaluation version and requires a new untouched
set.

## 8. Paired execution protocol

1. Generate all H1a-lite base completions without adaptive verification.
2. Assign a run ID before every model attempt and retain all attempts.
3. Freeze the base workspace, public evidence packet, trace, model manifest, and
   source hash.
4. Run the hidden grader out of band to create evaluation labels.
5. Apply every routing policy to the same base-completion population.
6. Replay adaptive actions in separate copies of the frozen workspace.
7. Grade the final artifact with the same grader version.
8. Aggregate prediction quality separately from repair effectiveness.

The routing implementation must not read the label table. Evaluation code joins
predictions and labels only after routing artifacts have been sealed.

## 9. Metrics

### Risk prediction

- false-completion precision, recall, and false-negative rate;
- risk-coverage curve and area under the risk-coverage curve;
- AUROC and average precision when both classes have sufficient support;
- calibration or Brier score only when probabilistic predictions and sample
  size make the estimate meaningful;
- results by task family and base model.

### Intervention

- final hidden task success;
- accepted false completions after policy execution;
- false completions recovered;
- repair success conditional on a true pre-escalation failure;
- unnecessary escalations and harmful repairs;
- hard-safety and protected-evidence violations.

### Cost

- verification-only input, cached input, uncached input, and output tokens;
- model calls, probe calls, wall time, and provider-reported cost when available;
- recovered false completions per model call and per 100,000 verification tokens;
- cost per final hidden success.

Raw token classes are kept separate. Total-token reductions alone do not imply
monetary savings.

## 10. Statistical reporting

The task, not an individual repeated trajectory, is the primary independent
unit. Report raw per-task outcomes and task-clustered bootstrap 95% confidence
intervals. For paired binary outcomes, also report the paired contingency table
and an exact paired test when sample size permits.

Wide intervals or a missed target do not authorize dropping tasks, replacing
runs, changing thresholds, or redefining a metric.

## 11. Claim gate

The primary selective-verification claim is eligible only if frozen held-out
results jointly show:

1. P5 reduces accepted false completion relative to P0;
2. P5 recovers more false completions than P2 at matched model-call budget;
3. P5 uses materially less verification compute than P1 at comparable final
   reliability, or occupies a non-dominated reliability-cost point;
4. P5 is not explained by P3 alone;
5. no hard-safety regression occurs.

Exact practical margins are chosen from development evidence and frozen before
held-out execution. If these conditions fail, ForgeBench remains a reproducible
engineering testbed and the paper claim is narrowed.

Cross-model transfer is a strengthening experiment, not a prerequisite for the
first Codex-focused portfolio result. Any cross-model claim requires a frozen
policy applied without model-specific retuning.

## 12. Related-work boundary

ForgeBench must not claim to introduce process-discipline evaluation, false
completion as a phenomenon, deterministic requirements testing, post-generation
verification, or adaptive test-time compute in general.

Closest comparison classes include:

- [RigorBench](https://arxiv.org/abs/2606.22678) and
  [AgentLens](https://arxiv.org/abs/2605.12925) for process quality after
  apparent success;
- [plausible-but-incorrect SWE-bench patch studies](https://arxiv.org/abs/2503.15223)
  and [Building to the Test](https://arxiv.org/abs/2606.28430) for incomplete
  validation signals;
- [SWE-Doctor](https://arxiv.org/abs/2607.00990) for multi-faceted runtime
  diagnosis;
- [RETRACE](https://arxiv.org/abs/2608.08950) for independent post-generation
  patch verification;
- [Scaling Test-time Compute for LLM Agents](https://arxiv.org/abs/2506.12928)
  for additional inference allocation;
- [Agentic Harness Engineering](https://arxiv.org/abs/2604.25850) for global
  harness optimization.

The scoped question is whether **public-evidence-only, per-completion routing**
produces a better held-out reliability-cost tradeoff than meaningful uniform
and equal-budget alternatives.

## 13. Freeze sequence

```text
Protocol v1
  -> development task expansion
  -> frozen base-completion format
  -> policy and probe development on dev only
  -> freeze policy manifest and practical margins
  -> freeze hashed held-out manifest
  -> execute held-out at most twice
  -> publish every attempted run and limitation
```

Changes after any freeze create a new protocol or policy version. They do not
overwrite prior results.

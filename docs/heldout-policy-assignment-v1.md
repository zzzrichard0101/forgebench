# Held-out Policy Assignment v1

Date: 2026-08-22  
Status: **frozen before policy replay**

## Outcome

ForgeBench assigned all six executable policies to the same 30 immutable
attempt-2 base completions. Planning used the frozen risk rules, probe adapters,
Random-k seed `1729`, public task contracts, and public workspace evidence only.
The sealed hidden label catalog was referenced by hash but never opened.

| Policy | Probe calls | Model calls |
| --- | ---: | ---: |
| Accept-All | 0 | 0 |
| Verify-All | 0 | 30 |
| Random-k call-matched | 0 | 9 |
| Probe-All | 30 | 0 |
| Risk-Model direct | 0 | 9 |
| Risk-Hierarchical | 9 | 9 |

- assignment manifest: `sha256:c275ccbe34243c90f8548f55ea6b48708a75124bdcab2c96b623365d06cb9083`;
- base catalog: `sha256:6fcbe9dddfb4ca11ebdc8078367a3e6f17b44c0b10ad25355583b086fcaee591`;
- opaque label catalog: `sha256:909099f0e3e132c61141b6308c0bf508faa481a410b4271c963349d264d51cec`.

## Pre-replay limitation

The public assignment itself exposes a degeneracy that must not be repaired
after seeing the held-out population:

1. all nine risk escalations occur in the `adversarial` family;
2. that family contains exactly nine bases;
3. task-family-stratified Random-k therefore selects those same nine bases;
4. no high-risk base has a supported hierarchical probe route, so every
   hierarchical probe route continues to a model call.

Consequently, Random-k and Risk-Hierarchical have identical model-selection
bits for all 30 bases. Their intervention context can still differ, but this
held-out run cannot cleanly support a claim that risk routing selected better
bases than random allocation. Risk-Hierarchical also collapses operationally
toward Risk-Model direct, with extra unsupported-probe overhead.

The assignments remain valid for comparisons with Accept-All, Verify-All, and
Probe-All and for reporting this negative design result. The frozen policy is
not retuned, the strata are not redefined, and hidden outcomes remain sealed.

## Next gate

Execute every policy from the exact manifest and reject any replay whose base
hash or observed routing differs. Hidden labels stay outside the runner and are
joined only after all replay artifacts have been sealed.

# Held-out Public-Policy Replay v1

Date: 2026-08-22  
Status: **60/60 complete without model or hidden grader access**

## Outcome

Accept-All and Probe-All replayed all 30 immutable bases from the frozen policy
assignment manifest.

| Policy | Completed | Infrastructure failure | Model calls |
| --- | ---: | ---: | ---: |
| Accept-All | 30 | 0 | 0 |
| Probe-All | 30 | 0 | 0 |

All 60 replay copies retained public Completion Gate eligibility. Every replay
record content hash verified, and sealed base hashes were checked before and
after each copy. No hidden task result was computed or stored.

- plan: `sha256:fa46fb9cfbbb25b87a74e3931919db36446cb5f58def2e88ff47d9affee38ba1`;
- raw execution: `sha256:972e4224648e001d1903960563aa96162ec12d594b57c0039ff22b59261cc76c`;
- replay record catalog:
  `sha256:a975a62650edbd74bfb60a541eec2d3817d89321894b859de2f92e9b1dfceaec`.

## Probe-All limitation

Probe-All selected a probe for every base, so 30 deterministic probe records
exist. However, the frozen probe adapter reported every route as unsupported.
The adapter requires both a transferable public contract and a triggered risk
signal whose evidence names the missing `file_type` dimension. None of the 30
base decisions satisfied that conjunction.

Thus Probe-All consumed no model tokens but also executed no effective contract
case. It cannot explain or challenge hidden reliability in this population.
Together with the assignment-stage Random-k degeneracy, this is a substantive
negative result about the current policy design rather than an infrastructure
failure. The probe policy is not changed after observing the held-out routes.

## Next gate

The remaining frozen policies require 57 model calls: Verify-All 30, Random-k
9, Risk-Model direct 9, and Risk-Hierarchical 9. Their runner must also defer
hidden evaluation, validate observed routing against the assignment manifest,
and seal every replay before the external labels are joined.

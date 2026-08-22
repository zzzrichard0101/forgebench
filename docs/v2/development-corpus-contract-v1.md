# V2 development corpus contract

Status: implemented; corpus empty  
Version: `v2-development-corpus-v1`

Stage A keeps two artifacts separate:

1. A public corpus manifest identifies frozen apparent completions, task
   clusters, repository lineages, public evidence, and content hashes.
2. An oracle catalog identifies the pre-intervention hidden outcome and failure
   mechanism. It is supplied only to the curator-side audit command and is
   never an intervention input.

Schemas:

- `benchmark/schema/v2-development-corpus.schema.json`
- `benchmark/schema/v2-development-oracle-catalog.schema.json`

Validator:

```text
python scripts/validate_v2_development_corpus.py \
  --public-root <v2-public-root> \
  --manifest <v2-public-manifest>
```

Adding `--oracle-catalog <external-path>` performs a curator-side aggregate
audit. The output contains counts and hashes, not case-level hidden outcomes.

## Enforced boundaries

- every base passed the public Completion Gate;
- public records contain no cohort, hidden outcome, mechanism, grader result,
  or known-good field;
- task, base, and public-evidence hashes match their files;
- all paths remain inside the declared public root;
- case IDs and base IDs are unique;
- one task cluster cannot map to multiple tasks or repository lineages;
- task IDs and seed revisions cannot overlap either the V1 development or V1
  held-out manifests;
- the oracle catalog targets the exact content-addressed public manifest;
- oracle labels join one-to-one with public cases;
- false-completion and passing-control labels are internally consistent;
- bases with pre-existing hard-safety violations are ineligible.

The validator reports `validation_gate_population_ready=true` only for a frozen
manifest containing at least 15 false-completion clusters, 15 passing-control
clusters, and six represented failure mechanisms on the
`mechanism_validation` split. This is population readiness, not a Stage A pass.

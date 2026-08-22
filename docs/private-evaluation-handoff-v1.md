# Private Evaluation Handoff v1

Date: 2026-08-22  
Status: **public request frozen; external evaluation pending**

## Purpose

This handoff binds the completed held-out experiment to exactly 30 immutable
base workspaces and 120 model-policy replay workspaces. It lets an independent
custodian run the unchanged private grader without exposing grader source,
known-good artifacts, hidden values, or outcomes to the policy-authoring
session before the public execution was sealed.

The machine request is
[`heldout-private-evaluation-request-v1.json`](../experiments/configs/heldout-private-evaluation-request-v1.json).
Its content hash is
`sha256:84311977af6e08884b7ab0bfbe83153237a9a2ed0a4d92cab19feeb3fc906132`,
and its 150-target catalog hash is
`sha256:e3eee4ad151787cc72e423d090683f3d4ecfbc8a8fb8b07ea19ccbad45ef138b`.

## Evaluation boundary

The independent evaluator must:

1. verify the request hash, private grader seal, sealed base-label catalog hash,
   target record hashes, and target workspace hashes;
2. join or reproduce exactly 30 base outcomes using the already sealed label
   catalog;
3. grade all 120 replay workspaces with the same private grader version;
4. run the grader's required repeatability and integrity checks;
5. emit only booleans and binding hashes in the result envelope defined by
   [`private-evaluation-result.schema.json`](../benchmark/schema/private-evaluation-result.schema.json);
6. keep the grader, labels, known-good materials, hidden values, and result file
   outside the public repository.

Accept-All and Probe-All receive the matching base outcome because neither
policy changed the base workspace. Verify-All, Random-k call-matched,
Risk-Model direct, and Risk-Hierarchical receive the outcome of their bound
replay workspace.

## Expected private result

The result must contain exactly 30 `base_outcomes` and 120 `replay_outcomes`.
Each outcome includes only its public identifier, the expected binding hashes,
`hidden_task_passed`, and `hard_safety_violation`. The envelope also attests
that hashes were verified, the grader version did not change, repeatability
checks passed, and private artifacts remained external.

The external session can validate the envelope with:

```powershell
$env:PYTHONPATH = "src"
py -3 scripts/validate_private_evaluation_result.py `
  --result "C:\absolute\external\private-evaluation-result-v1.json"
```

Do not copy that result into `experiments/`, `runs/`, or any Git-tracked path.
Return only its content hash, the two outcome counts, integrity status, and the
external file path needed by a separate final-analysis session.

## Interpretation already frozen

- Random-k and Risk-Hierarchical selected the same nine model-routed bases, so
  they cannot establish an allocation advantage over one another here.
- All nine hierarchical probes were unsupported and saved no model calls.
- Verify-All already caused one visible protected-file regression.
- No policy wins until the sealed outcomes are joined and uncertainty is
  reported at the task-cluster level.

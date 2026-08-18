# Held-out Intake Firewall v1

## Outcome

ForgeBench now has a two-party intake path for the ten-task held-out snapshot.
The independently authored public `heldout-v1` task package and its private
grader seal are now registered. Private grader implementations remain outside
the repository and were not inspected during public intake.

## Registered snapshot

- status: `accepted_not_executed`;
- tasks: 10 (`development` 4, `incident` 3, `adversarial` 3);
- transferable probe contracts: 3;
- public catalog: `sha256:8e726ea4f5523f34ac05afe01eb014a730f5eceb99a475ed34833d1c56a7ed34`;
- private seal: `sha256:aee74ae33f37d19c311c28066d877e88e55699335e12efc00d3570c0abddf632`;
- frozen policy: `sha256:1b779f87242da24975167f935540fe0107e963841d5a89cb5e96453e4f87e9ff`;
- declared held-out attempts used: 0 of 2.

The machine-readable registration is
[`experiments/reports/heldout-intake-v1.json`](../experiments/reports/heldout-intake-v1.json).
Registration confirms provenance and intake validity; it is not a performance
result. The next action is to generate and seal three shared base completions
per task before replaying the frozen comparison policies.

The private-side command hashes grader trees and emits only task IDs, hashes,
and an independence attestation. The public-side command deliberately has no
private-grader-root argument. It reads the seal but cannot inspect grader files.

## Required separation

### Independent custodian

The custodian authors or reviews the ten tasks and keeps grader files outside
the ForgeBench repository and outside the policy-author session. In that
environment they run:

```powershell
python scripts/seal_private_graders.py `
  --grader-root <private-grader-root> `
  --task-id <id-1> --task-id <id-2> `
  --custodian-id <reviewer-id> `
  --attest-untouched-seed-fails `
  --attest-known-good-outcome-passes `
  --attest-protected-mutation-detected `
  --attest-three-repeat-grade-deterministic `
  --output <private-seal.json>
```

All ten task IDs must be supplied. The seal output must be outside the grader
root. Symlinks and empty grader directories are rejected.
Each quality attestation flag is mandatory and represents a check performed in
the private environment, not a check repeated by the public intake process.

### Public intake

Only public task documents, seed repositories, and `private-seal.json` enter
the ForgeBench workspace:

```powershell
python scripts/validate_heldout_intake.py `
  --heldout-manifest <public-heldout-manifest.json> `
  --private-seal <private-seal.json> `
  --output <intake-result.json>
```

The intake fails unless all of the following hold:

- the already-frozen policy and every bound artifact remain unchanged;
- exactly ten tasks use the `test` split and have content-addressed seeds;
- the public manifest hash binds every task document;
- task IDs and seed revisions do not overlap development;
- all three task families are present;
- at least three tasks expose a registered transferable probe contract;
- the private seal has exactly the same task IDs and passes its independence
  attestation.

## Trust boundary

The seal is tamper-evident, not a cryptographic identity signature. The
custodian identity and independence statement remain a procedural trust claim
and must be named in the final report. ForgeBench must publish this limitation.

The policy author must not run the private sealing command on the real grader
root, inspect grader files, or request grader-derived hints. Any such access
invalidates held-out v1.

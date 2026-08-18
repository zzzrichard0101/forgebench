# ForgeBench Held-out v1

This directory contains the public half of the independently maintained
ForgeBench held-out v1 snapshot: ten test task documents and their immutable
seed fixtures. Private graders and known-good validation materials are excluded
from this repository and are represented only by the root-level
`private-seal.json`.

The snapshot covers development, incident, and adversarial work. Three tasks
publish the transferable `python_manifest_file_loader` probe contract. The
manifest content-addresses both every task document and every seed fixture.
The replacement-by-replacement comparison against the development catalog is
documented in [LINEAGE_AUDIT.md](LINEAGE_AUDIT.md).

The private seal is tamper-evident rather than a cryptographic identity
signature. Its custodian identity and independence statement are procedural
trust claims.

## Custodian record

- Custodian: `codex-independent-custodian`
- Review date: 2026-08-18
- Task-lineage review: completed against the frozen `dev-v0.6` catalog; no ID,
  seed revision, repository lineage, or trivial template variant was reused.
- Development grader access: the public repository made development graders
  available to the custodian; no development grader implementation or hidden
  case was copied into this snapshot.

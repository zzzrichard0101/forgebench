# ADR 0001: Copy-based workspace isolation for the first baseline

Date: 2026-08-16  
Status: Accepted

## Decision

Each run copies an immutable seed directory into a unique run-owned workspace.
All path-based tools validate resolved paths against that workspace.

## Rationale

This makes local development portable and prevents one run from modifying the
seed or another run. It is sufficient for deterministic smoke tests and early
benchmarks.

## Consequences

Path isolation does not provide OS-level process, network, or resource isolation.
Production-readiness claims therefore require a container or microVM boundary in
a later phase. Until then, the command tool stays allowlisted and network-free by
configuration.


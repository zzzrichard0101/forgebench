# ADR 0002: Append-only JSONL traces

Date: 2026-08-16  
Status: Accepted

## Decision

Every runner event is written immediately as one versioned JSON object per line
with a run ID and monotonic sequence number.

## Rationale

JSONL remains readable after interruption, streams naturally, and permits a
report row to be traced back to exact model and tool events. SQLite indexes can
be derived later without making the database the sole evidence store.

## Consequences

Payload schemas must be versioned. Sensitive values will need redaction before
provider adapters or production traces are enabled.


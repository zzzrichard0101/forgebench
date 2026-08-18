# Held-out v1 lineage audit

Review date: 2026-08-18. Reviewer: `codex-independent-custodian`.

The five replacements below use new IDs, new content-addressed seeds, and new
repository structures. The three transferable loaders share only the frozen
public adapter signature required for probe selection; their domain behavior
and validation flow differ.

| Replacement | Closest development task | Why this is not a trivial variant |
| --- | --- | --- |
| `regional-tax-table-loader` | `python-config-precedence` | The seed is a nested tax-engine package plus CSV data and a manifest. The work validates domain rows, uniqueness, numeric finiteness/range, and contained asset resolution; it does not merge configuration sources or implement precedence. |
| `campaign-template-bundle` | `python-plugin-boundary` | This loader never imports or executes selected content. It validates a nested HTML asset against a declared placeholder schema and repository containment, rather than enforcing a plugin code-execution trust boundary or copying plugin grader cases. |
| `rollout-allocation-loader` | `python-schema-bool` | The seed loads a TOML rollout plan from a package repository and enforces typed cohort allocation invariants whose total must equal 100. It is not JSON-schema boolean validation and uses a different data flow and failure surface. |
| `unicode-account-identifier` | `python-header-normalization` | The task applies Unicode normalization, category checks, and mixed-script safety to account registration. It does not canonicalize HTTP header names or resolve duplicate headers. |
| `database-migration-lock-incident` | `connection-leak-incident` | The evidence correlates lock modes, blocked services, transaction settings, and recovery timing to diagnose blocking DDL. It does not reconstruct connection acquisition/release lifecycles or count leaked pool connections. |

The replacement incident is also structurally distinct from
`worker-visibility-incident`: it uses a relational lock timeline and database
settings to produce remediation, not job visibility timeouts or worker retry
behavior. No replacement uses archive extraction, so the
`python-archive-boundary` structure is absent.

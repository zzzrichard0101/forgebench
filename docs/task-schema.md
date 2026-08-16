# Benchmark Task Authoring Specification v0.1

The canonical machine-readable schema is [`benchmark/schema/task.schema.json`](../benchmark/schema/task.schema.json).

Phase 1 task documents use JSON so validation works with the Python standard
library alone. YAML loading and full Draft 2020-12 JSON Schema validation are
added when the Phase 2 project environment is bootstrapped.

## Required properties

Every task defines:

- a stable, human-readable `id` and integer `version`;
- family, difficulty, and split;
- a seed repository source and immutable revision/hash;
- the instruction visible to the agent;
- execution budgets;
- visible public checks and hidden grader checks;
- safety policy and permitted capabilities;
- expected evidence artifacts;
- benchmark-author metadata that is not shown to the agent.

## Isolation contract

Before every run, the runner creates a new workspace from `seed_repo`. The evaluated agent sees only the task instruction, allowed repository content, public tests, tool schemas, and tool outputs. It cannot read:

- hidden grader source;
- expected patches or reference solutions;
- other agents' traces;
- test-split annotations;
- host credentials or files outside the run workspace.

## Grading contract

Checks have `required` or `diagnostic` severity. A task passes when all required checks pass and no hard safety event occurs. Check types initially supported are:

- `command`: argument-array execution with exit status and optional bounded output pattern;
- `file_exists`: required artifact path;
- `file_absent`: forbidden artifact path;
- `json_schema`: output file conforms to a schema;
- `workspace_policy`: changed-path and forbidden-operation audit.

Custom graders may be added later, but must return the common grader-result schema and pass deterministic fixture tests.

## Difficulty rubric

- `easy`: one localized fault or change; expected direct tool sequence;
- `medium`: cross-file reasoning, ambiguity resolution, or more than one invariant;
- `hard`: long-horizon work requiring recovery, replanning, hidden interaction, or competing constraints.

Difficulty is validated empirically after baseline runs. Any relabeling is versioned and recorded without changing task content.

## Author checklist

- [ ] The instruction describes a realistic outcome, not an implementation recipe.
- [ ] A known-good solution passes all checks.
- [ ] At least one plausible partial solution fails a required check.
- [ ] The grader does not require network access.
- [ ] The task has no secret or copyrighted private data.
- [ ] Public checks do not reveal every hidden invariant.
- [ ] The time and step budgets are sufficient for a competent agent.
- [ ] The seed revision and task content are immutable for reported runs.
- [ ] Safety traps, if any, are labeled in author-only metadata.

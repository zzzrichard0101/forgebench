# Independent Held-out Author Handoff

Create ten new ForgeBench tasks without reusing a development task ID, seed
revision, repository lineage, or trivial template variant.

Requirements:

1. Use the `test` split and cover development, incident, and adversarial
   families.
2. Include at least three tasks that independently fit the public
   `python_manifest_file_loader` probe contract. Do not copy the existing plugin
   fixture or hidden cases.
3. Keep grader implementations outside the ForgeBench repository and outside
   any policy-author session.
4. Demonstrate privately that each untouched seed fails, a known-good outcome
   passes, protected mutation is detected, and three repeated grades agree.
5. Deliver only public tasks, public seeds, a frozen public manifest with its
   catalog hash, and the private grader seal.
6. Do not reveal grader source, expected hidden values, known-good patches, or
   failure labels to the policy author.

The author or reviewer must record their identity, date, task-lineage review,
and whether they had access to ForgeBench development graders. Any discovered
overlap must be resolved before sealing rather than after evaluation.

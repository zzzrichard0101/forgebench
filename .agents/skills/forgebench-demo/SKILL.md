---
name: forgebench-demo
description: Prepare, run, verify, and record the public ForgeBench portfolio demo. Use for ForgeBench demo rehearsals or recording; do not use it to resume research waves or access private graders.
---

# ForgeBench Demo

Produce a short, honest demonstration of the public harness behavior and the
sealed V1/V2 conclusions. Treat demo preparation as portfolio packaging, not a
new experiment.

## Workflow

1. Work from the ForgeBench repository root and confirm the checkout is clean.
2. Run `python scripts/run_public_demo.py`.
3. Confirm that the first attempt passes public completion, is routed high risk,
   fails `plugin_non_python_regular_file`, and is blocked for repair.
4. Confirm that the explicitly scripted remediation passes the same public
   probe with zero model calls. Never describe it as a live agent repair.
5. Run `python -m unittest tests.test_public_demo -v` with `PYTHONPATH=src`.
6. Follow [`demo/5-minute-demo.md`](../../../demo/5-minute-demo.md) for the
   screen order and narration. Keep the public-demo terminal output visible for
   roughly 40 seconds.
7. Before delivery, verify that no generated file or private artifact entered
   the Git worktree.

## Evidence boundary

- Use only the committed public task and fixture.
- Do not open, copy, hash, summarize, or display external graders, labels,
  oracle catalogs, individual hidden outcomes, or raw private traces.
- Preserve the terminal disclosure: `PUBLIC FIXTURE ONLY | SCRIPTED
  REMEDIATION | NO PRIVATE GRADER`.
- Present V1 as a rejected policy claim and V2 as a preregistered Stage A gate
  that was not met. Do not imply a reliability improvement or Stage B result.
- A demo failure is a packaging problem. Do not change research thresholds,
  frozen populations, sealed reports, or terminal rules to make it pass.

## Recording standard

Target 1920x1080, 30 fps, 4:30-5:00, with Korean narration and English
technical artifacts. Use chapter captions `Question`, `Public Demo`, `Freeze`,
`V1`, `V2`, and `Decision`. Keep the repository URL visible for the last five
seconds.

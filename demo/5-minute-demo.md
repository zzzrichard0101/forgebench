# ForgeBench 5-minute demo

Audience: KRAFTON AI Research - AI Agent Engineer  
Goal: show harness engineering, evaluation discipline, and honest iteration in five minutes.

## Before recording

- Use a clean `main` checkout at or after commit `f344de9`.
- Keep the external private grader, labels, and result file closed and outside the repository.
- Set the terminal font to at least 16 px and browser zoom to 110-125%.
- Pre-open `README.md`, the final report, the final freeze, and the analysis module.
- Do not scroll through raw model traces or individual hidden outcomes.

## Timeline and talk track

### 0:00-0:35 - The engineering question

Show: repository README, title and current status.

Say:

> ForgeBench asks a narrow question: after a coding agent says it is done, can a
> harness decide when to spend more verification compute and reduce false
> completion? I built the runner, typed tool boundary, completion checks, risk
> routing, replay system, and leakage-controlled evaluator around that question.

Point out:

- one model and frozen inference settings;
- identical base workspaces across policies;
- deterministic public gates separated from the hidden evaluator.

### 0:35-1:20 - The harness, not a prompt demo

Show: `README.md` architecture description and `src/forgebench/`.

Say:

> The unit under test is the harness. Planning, tool execution, completion,
> deterministic probes, risk scoring, and model verification all produce
> trace-visible records. Every replay runs in a copied workspace and checks its
> source and final hash. This lets me distinguish agent failure, safety
> regression, and infrastructure failure instead of collapsing them into one
> score.

Open briefly:

- `src/forgebench/heldout_model_replay.py`;
- `src/forgebench/private_evaluation_handoff.py`;
- `src/forgebench/private_evaluation_analysis.py`.

### 1:20-2:05 - Reproducibility proof

Run:

```powershell
$env:PYTHONPATH = "src"
py -3 -m unittest tests.test_private_evaluation_analysis tests.test_heldout_final_evaluation_freeze -v
```

Show: the frozen request and final freeze hashes.

Say:

> Policy and thresholds were frozen before held-out execution. The public
> replay was sealed before any hidden outcome was joined. An independent
> process graded 30 bases and 120 replays, returned only a hash-bound result
> envelope, and kept graders and labels outside Git.

### 2:05-3:15 - The result, including failure

Show: `docs/heldout-private-policy-evaluation-v1.md`, result table.

Say:

> The proposed policy did not work. All 30 publicly complete bases were hidden
> failures, and none of 120 model-policy replays produced a hidden success.
> Risk routing found 9 failures, but verification repaired zero. Verify-All
> spent 30 model calls, still repaired zero, and introduced one hard-safety
> violation. I rejected the predeclared novelty claim instead of tuning on the
> held-out set.

Emphasize:

- P5: 9 model calls, 504,339 input tokens, 0/30 recoveries;
- risk recall: 0.30, task-cluster bootstrap 95% CI `[0.0, 0.6]`;
- 20,000 task-cluster bootstrap samples, seed 1729;
- no individual hidden trajectory or grader source is public.

### 3:15-4:15 - What the negative result diagnosed

Show: claim-gate section and machine-readable report.

Say:

> This result separates three problems. First, the base population was
> single-class: every public completion was false, so AUROC was undefined.
> Second, Random-k and both risk policies selected the same nine adversarial
> bases, so allocation novelty collapsed. Third, all hierarchical probes were
> unsupported, so probing saved no model call. The failure is therefore
> actionable harness evidence, not just a zero score.

### 4:15-5:00 - Why this fits AI Agent Engineer

Show: one-page portfolio PDF or README current-status block.

Say:

> The project demonstrates how I work on agent harnesses: make routing and
> completion explicit, design benchmarks before optimizing, preserve failed
> runs, separate private evaluation from policy development, and turn an
> unsuccessful hypothesis into a reproducible next decision. I would carry the
> same discipline into planning, memory, tool use, loop, evaluation, and
> meta-harness work at production scale.

Close with:

> My claim is not that this policy improved reliability. My claim is that I
> built an evaluation system capable of proving when it did not.

## Recording deliverable

- Target length: 4:30-5:00.
- Resolution: 1920x1080, 30 fps.
- Export one version with Korean narration and English code/report text.
- Add chapter captions: Question, Harness, Freeze, Result, Diagnosis, Role fit.
- Keep the repository URL visible in the final frame for five seconds.

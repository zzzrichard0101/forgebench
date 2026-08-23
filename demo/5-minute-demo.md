# ForgeBench 5-minute demo

Audience: KRAFTON AI Research - AI Agent Engineer  
Goal: show harness engineering, evaluation discipline, and honest stopping decisions in five minutes.

## Before recording

- Use a clean `main` checkout at or after the final portfolio-package commit.
- Keep external private graders, labels, oracle catalogs, and result files closed.
- Set the terminal font to at least 16 px and browser zoom to 110-125%.
- Pre-open `README.md`, both final reports, the final V2 aggregate, and the one-page PDF.
- Do not reveal raw model traces or individual hidden outcomes.

## Timeline and talk track

### 0:00-0:35 - The engineering question

Show: README title and final status.

Say:

> ForgeBench asks whether a coding-agent harness can distinguish apparent
> completion from correct completion and spend verification compute where it
> helps. I built the runner, typed tools, completion checks, recovery, risk
> routing, replay, benchmark, and leakage-controlled evaluator around that
> question.

Point out the fixed model, identical workspaces, deterministic public gates,
and private grader boundary.

### 0:35-1:20 - The harness, not a prompt demo

Show: `src/forgebench/` and the architecture section.

Say:

> The harness is the unit under test. Planning, tool calls, completion,
> deterministic probes, routing, and model verification all emit trace-visible
> records. Every run uses a copied workspace and verifies source and final
> hashes, separating agent, safety, and infrastructure failures.

Open briefly:

- `src/forgebench/heldout_model_replay.py`;
- `src/forgebench/base_completion.py`;
- `src/forgebench/v2_corpus.py`.

### 1:20-2:00 - Reproducibility proof

Run:

```powershell
$env:PYTHONPATH = "src"
python -m unittest tests.test_v2_screening_wave4_private_aggregate tests.test_heldout_final_evaluation_freeze -v
```

Say:

> Policies, task populations, thresholds, and terminal rules were frozen before
> evaluation. V2 retained all 90 slots. Private graders and labels stayed
> outside Git, and three external evaluations had identical oracle and grader
> result hashes.

### 2:00-2:50 - V1 rejected policy claim

Show: `docs/heldout-private-policy-evaluation-v1.md`.

Say:

> The V1 policy did not work. All 30 publicly complete bases were hidden
> failures, and none of 120 model-policy replays recovered one. Risk routing
> selected 9 failures but repaired zero. Verify-All repaired zero and introduced
> one hard-safety violation. I rejected the claim instead of tuning on held-out
> labels.

Emphasize: P5 used 9 model calls and 504,339 input tokens for 0/30 recoveries.

### 2:50-3:55 - V2 stopped before an invalid experiment

Show: `docs/v2/screening-wave4-private-aggregate-v1.md`.

Say:

> V2 asked a prerequisite question: is the repair-development population
> diverse enough to evaluate verifier allocation? Across four waves I froze 90
> Codex slots and externally graded 84 eligible bases. The passing-control gate
> passed with 27 clusters, but false completion reached only 4 of 6 clusters
> and 3 of 4 mechanisms. The final balanced Wave 4 added no false completion:
> all 28 eligible bases passed private grading.

Emphasize: no Wave 5, no relaxed threshold, and no Stage B activation.

### 3:55-4:30 - What the two negative results diagnosed

Say:

> V1 showed that more verification compute cannot repair an ineffective
> intervention. V2 showed that a benchmark must contain diverse target failures
> before an allocation claim is meaningful. ForgeBench separates policy
> failure, intervention failure, population failure, safety regression, and
> infrastructure failure rather than reporting one blended score.

### 4:30-5:00 - Why this fits AI Agent Engineer

Show: the one-page portfolio PDF.

Say:

> This project demonstrates how I approach agent harness work: make planning
> and completion explicit, bind evidence before reading outcomes, audit graders,
> preserve failed runs, and stop unsupported research. My claim is not that the
> proposed policies improved reliability. It is that I built a system capable
> of proving when they did not and why the next experiment was invalid.

## Recording deliverable

- Target length: 4:30-5:00.
- Resolution: 1920x1080, 30 fps.
- Record Korean narration with English code and report text.
- Add chapter captions: Question, Harness, Freeze, V1, V2, Decision.
- Keep the repository URL visible in the final frame for five seconds.

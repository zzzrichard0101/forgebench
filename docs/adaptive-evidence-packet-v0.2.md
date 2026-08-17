# Adaptive Evidence Packet Evaluation v0.2

Date: 2026-08-17  
Status: **focused replay improved; end-to-end input target not yet met**

## Goal

The first adaptive replay repaired the plugin false completion but consumed
97,108 additional input tokens because a new Codex process rediscovered the
repository. Evidence Packet v0.2 sends only:

- public task and check definitions;
- fired risk rules and missing contract dimensions;
- current changed text files and public tests;
- the public plan;
- a bounded verification recipe for each missing dimension.

The packet excludes hidden graders, `author_metadata`, and protected-file
contents. File content is capped at 24,000 characters and the emitted packet is
hashed in the run manifest.

## Recorded v0.1 failure

Run `4408df71ea0247ef9b5f0063b50ea218` reduced input to 64,172 tokens but failed
the hidden contract. The packet said `missing:file_type`, and Codex tested only
whether the entrypoint was a regular file. A regular `.txt` entrypoint remained
accepted.

The failure was preserved. v0.2 defines generic minimum probe sets per contract
dimension. For `file_type`, both a non-regular object and a regular file with a
different extension/category must be exercised. This is a development policy;
it does not expose the hidden grader result to Codex.

## Valid v0.2 result

Run: `f8e6bfe15c1f40afb99717a4221bedff`

| Metric | Full adaptive replay | Evidence Packet v0.2 | Delta |
|---|---:|---:|---:|
| Hidden task result | Pass | Pass | Preserved |
| Input tokens | 97,108 | 64,921 | -33.1% |
| Output tokens | 2,058 | 1,847 | -10.3% |
| Wall time | 53.858 s | 47.224 s | -12.3% |

The actual packet contained 2,506 file-content characters. Codex added both a
directory-entrypoint test and a non-Python regular-file test, then enforced a
regular `.py` entrypoint. Public checks, completion verification, and the hidden
grader passed. The source H1a-lite workspace remained unchanged.

## End-to-end interpretation

The packet improves the expensive second pass, but it does not yet make adaptive
input cheaper than H1a. Combining the historical plugin and archive H1a-lite
runs, the packet replay, and the low-risk archive routing gives:

| Metric | Historical H1a | H1a-lite + packet | Delta |
|---|---:|---:|---:|
| Input tokens | 382,459 | 412,176 | +7.8% |
| Output tokens | 8,309 | 7,622 | -8.3% |
| Wall time | 211.308 s | 201.688 s | -4.6% |

These calls were not temporally paired, so the comparison is descriptive. The
focused optimization succeeded relative to full replay, while the broader input
efficiency target remains unmet.

## Decision

Keep Evidence Packet v0.2 as the focused verification interface. Do not freeze
the held-out policy yet. The next cost reduction should remove model-led probe
rediscovery where possible: generate deterministic probe fixtures from the
dimension recipe, run them first, and call Codex only with the failing probe and
minimal affected files.

## Limitations

- This is one known development failure, not held-out evidence.
- One valid model call cannot estimate variance.
- Packet and full replay calls are stochastic and not paired.
- Historical H1a references are descriptive only.


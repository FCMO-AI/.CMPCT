# R36 — Regenerable-Deflate Project Wait-Owner Attribution Result

Status: **TERMINAL — `PROJECT_WAIT_OWNER_LOCALIZED`**

Frozen preregistration: `R36_REGENERABLE_DEFLATE_PROJECT_WAIT_OWNER_PREREG.md`.

Exact result-bearing evidence head: `078b9b11e95a876b7174239e59bc3fa38d168286`.

GitHub Actions run: `33846369660`, result-bearing job `100939273718`.

Immutable artifact: `v030-r36-project-wait-owner-078b9b11e95a876b7174239e59bc3fa38d168286`, artifact ID `9926800448`, ZIP SHA-256 `b237bde182a6ac38b1994f244b920de1385801385623e99b50ce7b9ad50e2f0d`.

## Terminal decision

R36 emitted **`PROJECT_WAIT_OWNER_LOCALIZED`** under the frozen cross-target law.

The same CMPCT-owned production frame is the sole qualifying localized owner on both protected targets:

- signature: `src/cmpct/builder.py:build`;
- representative line at the frozen evidence head: 272;
- full Incremental Backups candidate-minus-release median attributed wait-time delta: **+0.004398288 s**, with **+41** wait calls;
- isolated `snapshot_2.zip` candidate-minus-release median attributed wait-time delta: **+0.011841948 s**, with **+40** wait calls.

The nested delta clears the frozen **>=10 ms** floor and the full-target delta is positive, so the localization law is satisfied without threshold adjustment.

## Identity and byte evidence

All repetitions strongly verified and each arm was deterministic within the result-bearing run. `full-search` and `no-ordinary-zstd` were byte-identical on each target, while the candidate remained strictly smaller than `release-all-exact`:

| target | release-all-exact | byte-winning control | saving |
| --- | ---: | ---: | ---: |
| full-backups | 8,088,431 B | 8,056,015 B | **32,416 B** |
| nested-only | 2,231,162 B | 2,197,418 B | **33,744 B** |

The measured tree identities remained exact. This is causal/attribution evidence only; it grants no product or release credit.

## Diagnostic runtime evidence

Absolute R36 runtime is not product-speed evidence because `Condition.wait` was wrapped and stack capture perturbed the measured path. For completeness, the three-run medians were:

| target | release-all-exact | full-search | no-ordinary-zstd |
| --- | ---: | ---: | ---: |
| full-backups | 0.513987 s | 0.624093 s | 0.555187 s |
| nested-only | 0.351692 s | 0.483480 s | 0.411444 s |

The candidate's median wait totals were 0.077950 s / 61 calls on full-backups and 0.012157 s / 53 calls on nested-only, versus release medians of 0.073552 s / 20 calls and 0.000315 s / 13 calls respectively. The transferable result is the cross-arm attribution, not these instrumented wall times.

## Causal interpretation

The remaining synchronization debt is not distributed across generic Python threading machinery. Under identical instrumentation it maps to the CMPCT-owned candidate-encoding scheduling boundary inside `Builder.build`, where ordered parallel encoding currently consumes `ThreadPoolExecutor.map` results.

That narrows the lawful intervention from generic executor/thread tuning to one bounded project scheduling boundary. The frozen R36 interpretation therefore authorizes a lowest-sufficient Builder at that boundary only.

## Strongest surviving self-critique

R36 proves ownership of excess observed `Condition.wait` time under instrumentation; it does **not** prove that any particular replacement scheduling primitive will improve uninstrumented wall time. Stack capture and the wrapper itself perturb synchronization. A subsequent Builder must therefore use fresh-process, uninstrumented timing and may receive product credit only if it preserves exact byte identity to the byte-winning control, strong verification, hard locality, RSS, and the existing material-runtime law on both protected targets.

## Required next action

Freeze and execute one lowest-sufficient scheduling-boundary Builder. It may change only how the already-defined candidate encodes are awaited/collected inside `Builder.build`; it may not change candidate generation, codec policy, worker count, archive grammar, representation admission, thresholds, corpus, or locality accounting. Generic worker-count sweeps, arbitrary executor replacement, standard-library edits, workload/path dispatch, and threshold relaxation remain forbidden.

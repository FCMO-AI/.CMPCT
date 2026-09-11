# ONE-G0.2 packed observer fresh-process RSS — exact result at `0778b989` — 2026-09-08

Status: **`ADVANCE_PACKED_OBSERVER_RSS_SAFE` within a censored whole-process peak boundary.**

## Exact evidence authority

- source branch: `research/cmpct1`
- exact source SHA: `0778b989bc5d3ab5bd1d1290193d02283a8c7365`
- workflow run: `34220213608`
- job: `102041304331`
- artifact id: `10053463767`
- artifact name: `one-g02-packed-observer-rss-0778b989bc5d3ab5bd1d1290193d02283a8c7365`
- artifact digest: `sha256:19e7e08594970bbf30d4303ff092d1d08ea373bf609dac8ae31a1b4c20ea0dec`
- exact SHA binding, fresh-child reconstruction, frozen RSS gate and artifact retention: passed

## Frozen decision

- `semantic_gates_pass = true`
- `all_rows_rss_no_regression = true`
- `structured_rss_reduction = false`
- `decision = ADVANCE_PACKED_OBSERVER_RSS_SAFE`

All five 1 MiB families reported the same median absolute fresh-process peak for both arms: **93,460 KiB**, hence packed/eager = **1.0000x** everywhere.

| family | eager peak | packed peak | ratio | pre-writer peak | writer incremental peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| structured | 93,460 KiB | 93,460 KiB | 1.000x | 93,460 KiB | 0 KiB |
| compressed_like | 93,460 KiB | 93,460 KiB | 1.000x | 93,460 KiB | 0 KiB |
| long_runs | 93,460 KiB | 93,460 KiB | 1.000x | 93,460 KiB | 0 KiB |
| random | 93,460 KiB | 93,460 KiB | 1.000x | 93,460 KiB | 0 KiB |
| near_repeats | 93,460 KiB | 93,460 KiB | 1.000x | 93,460 KiB | 0 KiB |

## Hostile interpretation: the green result is censored

This result is useful but much weaker than “observer memory parity.” `ru_maxrss` had already reached 93,460 KiB **before** `_writer_once` began in every child. Neither eager Python opportunity materialization nor packed native state exceeded that pre-existing high-water mark, so the experiment cannot resolve their observer-local memory difference.

The main common-state censor is visible in the harness: before entering `_writer_once`, every 1 MiB child allocates source/target ctypes arrays and `(Segment * SIZE)()`. The native `Segment` layout occupies 12 bytes on the hosted ABI, so the segment arena alone reserves about **12 MiB** for a 1 MiB root, even on the frozen five-family matrix where relation admission is disabled and no segment plan is consumed. Interpreter/import/native-library state adds substantially more.

Therefore the exact claim is:

> packed handoff does not increase the measured full fresh-process peak above the current research writer's ~93.46 MiB common-state high-water mark.

It is **not** evidence that eager and packed observation have equal live memory, and it is not a structured-memory win. `structured_rss_reduction = false` must remain explicit.

## Observer state truth retained

At 1 MiB both arms temporarily reserve ~3,539,040 B of observer scratch during the native scan. Packed retained state after scan is:

- structured: 294,912 B;
- compressed_like: 0 B;
- long_runs: 5,280 B;
- random: 0 B;
- near_repeats: 24 B.

Those exact retained-state reductions are real, but they did not move `ru_maxrss` because the process had already crossed a much higher common peak.

## New memory debt exposed

The RSS gate has therefore found a different next owner: **common writer preallocation itself**. In particular, eagerly allocating a maximum `Segment * source_bytes` arena before relation admission wastes substantial live memory on relation-disabled roots. This is research-harness/native-writer debt, not a representation change.

A follow-up must compare eager segment-arena allocation against allocating segmentation state only after relation admission succeeds, while preserving exact plan/wire semantics on admitted hostile cases. That experiment must report current/live RSS as well as fresh-process peak so common startup state cannot censor the causal difference.

## Unchanged campaign authority

This memory result changes no stored bytes, reader semantics, selective-read amplification, recovery, portability, v0.29 or deferred-v0.30 authority. The 256 KiB packed speed regressions remain active debt and are being evaluated separately; this RSS green cannot wash them out.

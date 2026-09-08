# ONE-G0.2 one-slot small-vector observer handoff result — 2026-09-08

## Exact authority

- Branch at result source: `research/cmpct1`
- Experimental version: `ONE-G0.2`
- Exact result source: `b04cbb84b325fc8690634a3a3e145a1cd22cf2cc`
- Workflow run: `34221157507` (`CMPCT1 ONE-G0.2 small-vector observer`)
- Artifact: `10053981101` (`one-g02-small-vector-observer-b04cbb84b325fc8690634a3a3e145a1cd22cf2cc`)
- Artifact SHA-256: `63d18d0a6f3d1d3ce879cdbd3279efc8517908c5287cce40e39093e1be1c4b76`
- Result file: `one_g02_small_vector_observer.json`
- Decision: **`ADVANCE_SMALL_VECTOR_OBSERVER`**

The workflow completed successfully. The frozen executable returns zero only for `ADVANCE_SMALL_VECTOR_OBSERVER`; the retained JSON independently records the same decision.

## Mission lock

The candidate keeps the same native observation scan and changes only the transient writer handoff representation:

- zero opportunities: no retained payload;
- exactly one run/reuse opportunity: one inline scalar slot;
- two or more opportunities: the previously rehabilitated exact used-prefix packed representation.

This is writer-internal transient state. It is not ONE wire syntax, a reader opcode, a persisted cache, or a separate compression mechanism. There is no source-size selector.

## Frozen matrix and gates

Each `(size, family)` row ran in a fresh subprocess with 21 paired alternating repetitions.

Sizes: 256, 384, 512, 768, 1024 KiB.

Families: `structured`, `compressed_like`, `long_runs`, `random`, `near_repeats`.

Advancement required:

1. every `near_repeats` row wall and CPU hybrid/eager <= 1.05;
2. `structured` at 1 MiB wall and CPU <= 0.60;
3. no row in the complete 25-cell matrix above 1.05 on wall or CPU;
4. exact observer materialization, opportunity counts, relation signature, segment plan, Program, canonical wire/stats, roots and reconstruction.

All gates passed.

## Measured result

### The exact-one-record debt is closed

`near_repeats` emits exactly one 24-byte run record on every tested size, so the inline path is exercised on every row.

| Size | Wall hybrid/eager | CPU hybrid/eager |
|---:|---:|---:|
| 256 KiB | 0.994188x | 0.994139x |
| 384 KiB | 1.000875x | 1.000879x |
| 512 KiB | 1.003588x | 1.003558x |
| 768 KiB | 1.000730x | 1.000710x |
| 1 MiB | 1.003083x | 1.003068x |

The earlier packed-prefix debt on this family had been ~1.115x at 256 KiB, ~1.114x at 384 KiB, ~1.102x at 512 KiB and ~1.097x at 1 MiB. The structural one-slot path therefore removes the prior >5% regression without a source-size threshold.

### The opportunity-heavy bulk win is preserved

`structured` remains on the packed bulk path and is much faster than eager Python opportunity materialization:

| Size | Wall hybrid/eager | CPU hybrid/eager | Opportunities |
|---:|---:|---:|---:|
| 256 KiB | 0.346119x | 0.346741x | 3,072 |
| 384 KiB | 0.334730x | 0.334867x | 4,608 |
| 512 KiB | 0.337970x | 0.337224x | 6,144 |
| 768 KiB | 0.331320x | 0.331507x | 9,216 |
| 1 MiB | 0.333843x | 0.334043x | 12,288 |

At 1 MiB the median charged writer interval falls from about 24.008 ms to 8.015 ms wall while preserving byte-identical Program/wire semantics.

### Controls and strongest residual debt

`compressed_like` and `random` emit zero observer opportunities and remain near parity across the matrix. Their worst wall ratios are ~0.9995x and ~1.0040x respectively.

`long_runs` uses the packed bulk path with a modest number of records. It is the strongest residual warning:

| Size | Wall hybrid/eager | CPU hybrid/eager | Opportunities |
|---:|---:|---:|---:|
| 256 KiB | 0.970631x | 0.970678x | 55 |
| 384 KiB | 0.967711x | 0.967723x | 83 |
| 512 KiB | 1.034819x | 1.034864x | 110 |
| 768 KiB | 1.023035x | 1.024253x | 165 |
| 1 MiB | **1.048161x** | **1.048136x** | 220 |

The 1 MiB row is only ~0.002 below the frozen 1.05 veto. This result therefore advances the one-slot mechanism but does **not** justify multiplying inline-slot variants or fitting a new record-count crossover after seeing the data.

## Resource and semantic truth

- All 25 semantic rows passed.
- Canonical wire bytes, Surprise bytes, roots and reconstruction are unchanged between arms.
- The same native observer scan is used in both paths.
- Both paths still pay the same worst-case native scratch allocation during scanning. This experiment earns no RSS claim.
- `retained_output_bytes` is logical native record payload, not process peak memory.
- Downstream relation admission/segmentation still does not consume the observer opportunities in this harness. The result advances transient handoff economics only.

## Hostile review / strongest self-critique

The mechanism is causally cleaner than a source-size dispatcher because exactly-one storage is a structural representation boundary. However, the `long_runs` result demonstrates that packed-prefix handoff overhead can still become marginally unfavorable for modest opportunity counts. Adding two-slot, four-slot, eight-slot, or fitted count thresholds would risk rebuilding a handoff zoo around benchmark crossovers.

The stronger next hypothesis is therefore not “find the next inline capacity.” It is to make observation evidence directly useful to downstream discovery/admission/segmentation, so the writer stops charging a transient observer representation that is then ignored.

## Decision

**Advance the one-slot small-vector observer handoff as the preferred current transient observation shape.**

Do not claim product ingest, RSS, stored-byte, reader, recovery, portability, v0.29 or deferred-v0.30 authority from this result. No Genesis scoreboard point is earned.

# ONE-G0.2 compact observer handoff writer preregistration — 2026-09-08

## Mission lock / referee

The exact-head stage-owner profile selected `native_observe` for the next writer-speed budget, while the repaired observer-boundary decomposition showed that eager Python opportunity materialization can exceed the native C scan on opportunity-rich inputs. The positional observation cache remains demoted. This experiment asks one narrower question before any new C optimization: can the current writer keep the same native observation semantics and native output buffers while deferring the Python `Observation` graph, and does that materially improve the *whole current research-writer envelope*?

This is not a new ONE representation or opcode. The reader remains unchanged and performs no discovery. The compact view is writer-internal transient state only.

## Falsifiable hypothesis

Against the current eager boundary

`native scan -> ctypes output arrays -> Python Run/Reuse objects -> Observation -> unchanged writer`

a compact boundary

`native scan -> same ctypes output arrays/counts/stats -> unchanged writer`

will preserve exact observer semantics when materialized out of band, preserve relation classification/segment plan/Program/canonical wire/reconstruction exactly, and reduce whole-writer wall and CPU cost on opportunity-rich 1 MiB roots without materially regressing low-opportunity controls.

The experiment deliberately does **not** change the C observer kernel, input copy, output capacities, admission kernel, segmentation kernel, Program construction, validation, or canonical emission. This isolates eager Python opportunity materialization.

## Frozen matrix

Paired alternating A/B timing, 15 repetitions per arm, at 256 KiB and 1 MiB. A 4 KiB fixed-overhead control is also retained but does not vote for advancement.

Target families are deterministic and content-derived rather than workload labels in the mechanism:

- `structured`: repeated short records plus long constant regions;
- `compressed_like`: deterministic zlib output from mixed repeated/random payload;
- `long_runs`: alternating large constant runs;
- `random`: seeded incompressible bytes;
- `near_repeats`: repeated 64-byte motifs with sparse deterministic damage.

For the temporal writer, each target is paired with a same-length seeded independent previous root. Relation admission may accept or reject according to its unchanged frozen rules; the same classification must occur in both arms.

## Hard semantic gates

For every row:

1. `compact_view.materialize() == observe_native(target)` on an untimed authority path.
2. Relation classification, proof result, and native segment plan are identical across arms.
3. Program and canonical wire bytes/stats are identical across arms.
4. Decoding reconstructs both previous and current roots byte-exactly.
5. Root SHA-256 identities are unchanged.

Any semantic failure returns `INVALIDATE_COMPACT_OBSERVER_HANDOFF` and no performance interpretation is allowed.

## Frozen performance gates

Only 1 MiB rows vote for advancement.

Opportunity-rich rows are `structured`, `compressed_like`, and `long_runs`:

- median candidate/control wall ratio <= **0.90** on at least 2 of 3 rows;
- median candidate/control CPU ratio <= **0.90** on at least 2 of 3 rows;
- no opportunity-rich row may exceed **1.05** wall or CPU.

Low-opportunity controls are `random` and `near_repeats`:

- every control must remain <= **1.05** wall and <= **1.05** CPU.

The candidate must create **zero Python `RunOpportunity` / `ReuseOpportunity` objects in its timed observer boundary**. Out-of-band materialization used for semantic proof is excluded from timing and reported separately as authority work, not hidden writer work.

The benchmark records native output capacity and used bytes so a speed result cannot hide the already-observed worst-case buffer reservation. No memory-cap claim is earned from modeled bytes alone; process RSS requires a separate subprocess measurement before product promotion.

## Decisions

- `ADVANCE_COMPACT_OBSERVER_HANDOFF` only if all semantic gates and all frozen performance gates pass.
- `HOLD_COMPACT_OBSERVER_HANDOFF` if semantics are exact but performance gates fail.
- `INVALIDATE_COMPACT_OBSERVER_HANDOFF` on any semantic disagreement.

A pass promotes this compact handoff only as the next writer-internal implementation direction. It does not prove that downstream admission/segmentation *uses* observer opportunities yet, does not establish product writer speed/RSS, does not change stored bytes or reader semantics, and earns no v0.29/v0.30 Genesis scoreboard point by itself.

## Hostile-review traps fixed in advance

- alternate A/B order to reduce drift;
- disable cyclic GC consistently during paired timing;
- do not destroy the prior arm's large result inside the next arm's timer;
- compile/warm native libraries outside result timing;
- do not precompute a compact view outside the candidate timer;
- charge identical SHA-256, admission, segmentation, Program, validation and emission work in both arms;
- do not count untimed authority materialization as a candidate speed benefit;
- preserve the demoted cache as negative evidence rather than using it as a fallback.

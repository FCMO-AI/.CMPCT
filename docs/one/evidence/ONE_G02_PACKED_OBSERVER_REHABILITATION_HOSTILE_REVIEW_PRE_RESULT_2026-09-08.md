# ONE-G0.2 packed observer rehabilitation — hostile review before result

Status: pre-result review; thresholds frozen by `ONE_G02_PACKED_OBSERVER_REHABILITATION_PREREG_2026-09-08.md`.

## Strongest attack on the hypothesis

The previous `HOLD_COMPACT_OBSERVER_HANDOFF` result does not prove that retained worst-case arenas caused the low-opportunity regressions. Both arms already allocate/zero the same arenas during observation, and freeing a ctypes array may itself have little direct cost. The ~1.04–1.08x reds could instead come from allocator state, object lifetime effects, timing noise, or the fact that the compact handoff currently has no downstream consumer. Packing introduces another copy, so it can lose even if retention was part of the problem.

The experiment therefore keeps all prior hostile rows and requires complete 1 MiB <=1.05 closure rather than assuming the mechanism explanation is true.

## Why this is a causally different rehabilitation rather than threshold tuning

The prior compact candidate carries `run_capacity/reuse_capacity` arrays sized from the source length until the whole writer result is released. At 1 MiB this is ~3.54 MiB even when zero opportunities are discovered. The packed candidate copies only the used prefixes after the same native scan and permits those scratch arenas to die before admission/segmentation/Program/validation/emission.

The prior result remains immutable and red. No previous threshold, family, timing boundary or semantic gate is changed.

## Benchmark-design attacks

1. **`compressed_like` naming is not authority.** The prior exact result observed zero native opportunities there. It remains a no-regression row; it is not used to claim an opportunity-rich mechanism win.
2. **Structured alone cannot authorize a general handoff.** The new gate preserves its large gain but also requires every 1 MiB family to recover <=1.05 wall and CPU.
3. **Packed copy must be charged.** `ctypes.string_at` prefix copies occur inside `observe_native_packed()` and therefore inside candidate timing.
4. **Scratch destruction must be charged naturally.** The worst-case arrays are local to `_run_native`; their release occurs as the packed boundary returns. No prebuilt packed view is supplied to timing.
5. **No Python-opportunity smuggling.** Candidate timing returns compact bytes/counts/stats only. `materialize()` is authority work outside timing.
6. **No RSS fiction.** `retained_output_bytes` is exact retained native-record payload, not process RSS or Python heap size. A pass requires a separate subprocess RSS experiment.
7. **No downstream-consumption fiction.** Current relation admission and segmentation still consume source/target directly. A pass only proves dead Python materialization can be removed economically in the charged envelope.
8. **Source-sized input copy remains.** This experiment does not solve the ctypes input-copy boundary. Both arms pay it.

## Semantic attacks

- `PackedObservationView.materialize()` reconstructs `_CRun`/`_CReuse` arrays from packed bytes and must equal `observe_native()` on empty, tiny, structured, random, compressed-like and near-repeat inputs.
- Parameter validation and non-default `min_run/chunk_size/max_index_entries` must remain exact.
- Packed retained bytes must equal the exact used native record bytes and never exceed scratch capacity.
- The whole-writer relation signature, plan, Program, canonical wire, roots and decoded bytes must remain exact.

## Resource interpretation

A 1 MiB low-opportunity root should retain approximately zero native opportunity bytes after packing even though the scan temporarily reserves ~3.54 MiB. A structured root may retain hundreds of KiB because those are real discovered opportunities. This is a lifetime reduction, not an elimination of peak scan scratch.

A later production shape should avoid worst-case scratch reservation entirely or reuse bounded arenas, but that is deliberately not mixed into this falsifier.

## Pre-result decision discipline

- Pass only under the preregistered gain-retention + all-row no-regression rules.
- Preserve a red result if packing fails; do not add a size/opportunity threshold after seeing it.
- If packed passes, next measure subprocess peak RSS and then test a native observation -> admission/segmentation consumer so compact state is useful rather than merely non-materialized.

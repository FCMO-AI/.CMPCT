# ONE-G0.2 — fused cache versus native fresh observer preregistration

Date: 2026-09-07
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission lock / referee

The fused observation cache previously demonstrated large wall/CPU reductions against the Python fresh observer. The branch now contains a semantically equivalent native fresh observer. The prior comparison is therefore no longer strong enough to establish that incremental reuse removes intrinsically expensive work rather than mainly bypassing Python interpreter overhead.

This experiment directly compares **cached incremental observation** against **competent native fresh observation** on identical current bytes and identical ONE observation semantics.

No reader-visible representation, wire bytes, Law vocabulary, Surprise semantics, comparator setting, or product requirement changes in this experiment.

## Falsifiable hypothesis

For multi-block exact-repeat and sparse-update workloads, the existing fused cache will retain a material creation-time advantage over the native fresh observer while reconstructing exactly the same `Observation`.

A material advantage is preregistered as:

- exact repeat and one-block sparse edit: cached/native median wall **and** CPU <= `0.90x`;
- dispersed eight-block sparse edit: cached/native median wall **and** CPU <= `0.95x`;
- no productive row may exceed `1.05x` wall or CPU;
- a byte-shifted insertion is a hostile control, not a productive cache case; it must preserve exact semantics and remain <= `1.25x` wall and CPU;
- persistent cache payload remains explicitly reported and must remain <= `0.20x` of the base root size.

The timing matrix uses paired alternating order, 15 repetitions, 256 KiB and 1 MiB roots, and structured, seeded-random/incompressible, and already-compressed-like families.

Cache construction for the **previous** version is outside timed current-version samples because it is persistent writer state produced by the prior generation. Current-version validation, cache integrity work, replay, exact reuse proof, and changed-block recomputation remain inside the cached timed call.

Native compilation/warmup is outside timed samples for the same reason ordinary library initialization is not charged repeatedly to every observation call.

## Disproof / decision rule

`ADVANCE_CACHE_OVER_NATIVE` requires all semantic, payload, productive-row, and hostile-control gates above.

If semantics remain exact but the cache fails the productive timing gates, the experiment returns `DEMOTE_CACHE_PROMOTE_NATIVE_BASELINE`. In that case the cache is not deleted: its positive historical evidence remains useful for future update regimes or a compact/native cache implementation, but **new general observer-speed research should move to the native fused fresh path rather than adding more Python cache machinery**.

If semantic parity fails, return `INVALIDATE_COMPARISON` and repair semantics before drawing any performance conclusion.

## Hostile reviewer notes

This experiment deliberately attacks the strongest confound in the prior result: Python versus native implementation quality.

It does **not** prove total-writer acceleration. Even a cache win here must later survive the broader ingest envelope with authentication/root identity, opportunity admission, segmentation, Program construction, validation, direct canonical emission, placement, peak RSS, and memory/source traffic charged.

Conversely, a cache loss here does not prove incremental computation is fundamentally useless. It falsifies the **current fused-cache shape** as the preferred general observer-speed path against a competent fresh baseline.

Do not loosen thresholds after results are visible. Preserve negative rows and the exact result-bearing SHA.
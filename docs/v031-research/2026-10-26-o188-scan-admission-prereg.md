# O188 — scan-resistant decoded-cache admission (preregistration)

Date: 2026-10-26 UTC. **PROSPECTIVE, before instrument implementation or measurements.**

## Authority / isolated ownership
Canonical release v0.30.0 / physical revision 24; stacked on O175/#510 exact `eb4b2b249e50a2bf9995c760e3763a8f7fcc74fc` (O173/#509 and O169/#506 are source owners). Existing genuine-Reader O175 same-archive Linux A-B-B-A directly measured a retained-memory improvement (~14.99% peak RSS) and second-pass wall regression (~25.61%) for 96×1MiB forward scans, comparing historical unbounded and 64MiB LRU. This O188 branch owns **only a lower-rung independent admission-policy research oracle**, not a second Reader implementation, official benchmark, source-custody change, or release.

## Primary falsifiable question
Does an inexpensive *online* bounded-admission policy offer material headroom against the exact forward-scan LRU pathology, while retaining credible behavior on warm fits, hot-interleaved streams, cold scans, and changed working sets? A result on a synthetic trace cannot establish that changing CMPCT improves RSS/wall/CPU, only whether candidate-policy families deserve a true installed-Reader experiment.

## Choices / predictions (declared before outcomes)
1. Actual O169 LRU semantics (64MiB/32768 keys; weighted bytes).
2. **Fixed-pin admission**: fill 64MiB and thereafter bypass misses; strongest simpler scan-resistant control but susceptible to stale cache.
3. **Guarded 48/16 admission**: on first arrival retain at most 48MiB in a protected first-fill region; remaining 16MiB probationary LRU; protected entries stay until a bounded prolonged no-protected-hit reset (128 consecutive cache misses), thereafter first-fill anew. This is an exploratory **fixed**, not tuned, ratio/reset constant. No decoder-visible metadata, future traces or oracle gift can influence admission.
4. No-cache: zero retention, complete miss cost.
5. An ideal offline clairvoyant 64MiB comparator: **non-product upper bound**, allowed to see future but must respect 64MiB capacity and read-count accounting. Use only on the uniform 96-object scan; offline maximum possible second-pass hits is <=64.

Predeclared hypothesis: guarded admission on 96×1MiB forward scan ×3 yields >=48 hits in the second pass versus plain LRU's 0, with at most 64MiB retained; fixed-pin gets up to 64. If guard loses exactness/accounting or is worse than plain LRU on the 64MiB repeated-fit control, reject immediately. A phase-shift scenario that leaves old protected bytes after >=2 full traversals is a clear narrowing/failure even if the O175 scan improves. Fixed-pin is a strong competing control; if it equals/bests guarded across regimes, do not productize guard. Do not claim a Pareto or generic gain based only on chosen synthetic traces.

## Frozen deterministic trace families
- T1: `scan96`: 96 distinct 1MiB keys; three complete ascending passes (O175 workload shape).
- T2: `fit48`: 48 distinct 1MiB keys; three ascending passes.
- T3: `hot16_scan96`: one warm pass over 16 hot 1MiB keys, then (16 repeated hot accesses + 96 one-pass cold keys) × 3, cold keys always novel.
- T4: `phase_shift96`: 96 distinct A-keys twice, then disjoint 96 B-keys four passes; report each B pass explicitly.
- T5: `streaming_unique`: 512 unique 1MiB keys, no reuse (metadata/caching overhead without benefit).
- T6: `mixed_weighted`: 8 frequent 4MiB virtual ZIP equivalents plus unique 1MiB RAW objects, repeated waves; charge cache capacity by returned bytes and count miss count/weighted refetch work without presenting synthetic CPU as measured product CPU.
- T7: `tiny_items`: 40000 unique zero-byte keys, testing the 32768-entry cap.

Deterministic integer/key traces, no random selection or benchmark identity-based policy. Report per-family misses, hits, retained bytes, entry count, ideal upper bound where defensible, hypothetical refetch-byte proxy (not actual CPU), and negative cohorts. Preserve evaluator and original O175 measurements unchanged.

## Alternative explanations and kill/narrow
The O175 CPU regression may be dominated by Python overhead, mmap and CRC rather than cache policy; no offline model can prove a product speedup. A protected cache can appear good merely by preferring the first portion of a deterministic scan and fail under temporal shifts. If guarded loses to fixed-pin on all relevant decisions, or causes unacceptable phase staleness, stop before implementation and favor a simpler control or other frame. No new RDE policy lesson without repeated transferable evidence.

## Evidence rung, scope and concurrency
Rung: **derivation + deterministic offline policy oracle**. Later productization requires genuine exact-source installed Reader, real physical r24 corpus, repeat ABBA, RSS/wall/CPU, VZIP and concurrency, cross-platform and official product admission; no lower-rung result is release credit. Check open PR #506/#509/#510/#516 before writes, do not modify their branches. Detailed outcome appended separately; this prereg is immutable. No shared discovery-state mutation unless decision-changing truth has been reconciled.

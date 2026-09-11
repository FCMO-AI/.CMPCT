# ONE-G0.2 — Tail-return 8 KiB dispatch rehabilitation

**Branch:** `research/cmpct1`  
**Exact source:** `d2bb939a643dc8dd3283ae58ea813332b5d583ef`  
**Workflow run:** `33941709406`  
**Result-bearing job:** `101240308228`  
**Artifact:** `9962040269`  
**Artifact ZIP SHA-256:** `84f07176c3cb3a4d9321e0cd9728ea3433dd90973175ffd7abf8f7bcd897389f`  
**Experimental version:** `ONE-G0.2`

## Rehabilitation target

The first 8 KiB dispatcher was rejected because it wrapped the chosen selector in an extra call and copied its result field-by-field. This superseding Builder kept the previously frozen 8,192-byte opportunity boundary and the exact same timing gate, but made the result prefix ABI-compatible and directly returned the selected selector call.

## Static integration result

The same-compiler diagnostic supports the intended implementation mechanism:

- dispatcher body: **25 instructions**;
- `call` instructions: **0**;
- jump instructions: **4**;
- relocations to both counter and offset-only selector targets are present;
- decision: **`tail_shape_supported`**.

So the large field-copy/call debt of the rejected wrapper was genuinely removed at generated-code level.

## Paired timing result

**Frozen decision: `tail_size_dispatch_inconclusive`.**

Correctness remained exact: **50/50 ONE tests passed**, independent Python anchor traces matched, final Gear state/positions-considered matched, the frozen path selection was exact, and selected reserved-state accounting stayed exact.

The small counter path improved dramatically relative to the rejected wrapper. Representative medians were close to parity: 4,159-byte random **0.9966x**, repeated **0.9947x**; 4,160-byte random **0.9945x**, repeated **0.9942x**, zlib-like **0.9954x**; 8,191-byte random **0.9967x**, repeated **0.9992x**. Thus the earlier 1.074x repeated-4,159-byte integration debt did not survive the rehabilitation.

However the offset region did not satisfy the unchanged promotion law. At the nominal 8 KiB boundary the three regime medians were **1.0533x, 1.0817x, and 1.0499x** counter. At 16 KiB they were approximately **1.0232x, 1.0294x, and 1.0243x**. By 64 KiB the medians were near parity/slightly slower (**1.0058x--1.0127x**). The large region becomes favorable again:

- 262 KiB medians: **0.9622x, 0.9700x, 0.9649x**;
- ~1 MiB medians: **0.9362x, 0.9409x, 0.9401x**.

Cross-large median was **0.951549x**, narrowly missing the frozen `<=0.95` promotion threshold. No frozen reject condition fired, hence inconclusive rather than rejected.

Selected large-region state remains **41,056 B vs 49,248 B**, a **16.63% reduction**.

## Hostile review

The result disproves the simple story that wrapper field-copy alone explained the integrated timing gap. It did explain the tiny counter-path debt, but the same offset-only kernel's relative speed moved substantially when linked into a different shared-object composition. That makes **code-layout/compiler/link placement sensitivity** a live confounder. Choosing a new size threshold from this run would therefore be threshold tuning on unstable execution placement, not mechanism progress.

The next decisive diagnostic must compile counter, direct offset, and tail-dispatch together in one exact binary and pair them within the same run. It should determine whether `dispatch/direct-offset` is near 1.0 while `direct-offset/counter` changes with binary composition. If so, the problem is code layout/alignment/frequency behavior, not dispatch semantics; then alignment/LTO or fused integration is the legitimate target. If dispatch itself remains materially slower than direct offset in the same binary, the remaining wrapper branch/tail-jump is the target.

No research baseline is promoted. The counter selector remains authoritative until a superseding frozen gate passes. This creates no reader, Law, wire, stored-byte, product-speed, v0.29/v0.30, release, or superiority authority.

# ONE-G0.2 cold-rescue native cascade — hostile pre-result review (2026-09-05)

Status: **pre-result static review**. This note is intentionally persisted before consuming any result-bearing timing artifact for the frozen cold-rescue native cascade.

## Mission lock

The frozen experiment asks whether, after shared-observer silence, a bounded phase certificate plus sparse gate can preserve the four known true rescues while reducing native elapsed work relative to eagerly running the exact safe relation dispatcher on all 34 shared-silent pairs.

This review does not alter the frozen gate or implementation. It audits the claimed cheapness of the front end from source code and accounting alone.

## Falsifiable concern

**Hypothesis:** the current phase-certificate front end is too memory- and arithmetic-heavy to function as a cheap rejection stage against the already sparse exact dispatcher, even if it materially reduces full exact-proof executions.

**Disproof:** native timing can reject this concern if the frozen cascade reaches its preregistered median `gated/eager <= 0.90`, no size exceeds `1.05`, all four required positives are retained, and full exact executions stay within the frozen `<= 60%` bound.

## Static traffic bound

The current native phase certificate uses five source phases `{0,1,2,30,31}` at stride 32 and then scans the target at stride 32. Each sampled position loads and hashes one 8-byte word.

Ignoring end effects, this is:

- source: `5 * (n/32) * 8 = 1.25n` payload bytes read;
- target: `1 * (n/32) * 8 = 0.25n` payload bytes read;
- total phase payload sampling: approximately **1.50n bytes** per candidate pair.

The exact safe dispatcher coverage scan instead samples once every 64 bytes. For each sample it charges 2 bytes for zero-shift comparison and, only when zero-shift fails, at most four additional two-byte shifted comparisons. Therefore its coverage scan is bounded above by:

`(n/64) * 10 = 0.15625n` counted comparison bytes,

before its bounded proof stage. The phase front end therefore performs about **9.6x** as much modeled payload sampling as the eager dispatcher's worst-case coverage scan (`1.50 / 0.15625 = 9.6`), while also computing a 64-bit mixer, maintaining five bottom-4 heaps, sorting up to 20 witnesses, binary-searching them for every target sample, and possibly performing exact 8-byte witness compares.

This does **not** prove a 9.6x elapsed loss: counted comparisons and physical cache traffic are not identical, and the eager arm may enter additional proof work. It does show that `fewer exact proofs` is a weak proxy here. The cascade can reduce proof count and still lose badly in CPU time and memory traffic.

## Causal interpretation if timing fails

If semantic retention is exact but elapsed fails, the likely mechanism-level conclusion is **not** that opportunity gating is wrong. It is that this phase certificate is being recomputed as a standalone scan and therefore violates the intended fused-observation economy.

The next Builder should then avoid threshold tuning and avoid adding more certificate witnesses. It should attempt one of these same-principle repairs:

1. derive bounded-shift evidence opportunistically from state already produced by the promoted observation pass, so there is no second 1.5n scan; or
2. use a truly sublinear cold probe whose maximum touched bytes are statically bounded well below the eager dispatcher's coverage scan, then fall through to exact proof only on support.

Any replacement must preserve the four frozen rescues and the negative controls. The reader remains unchanged and performs no discovery.

## Hostile-review warning

A result that passes the `<=60%` exact-execution fraction but misses the elapsed gate is a **negative efficiency result**, not a near-win. Do not tune thresholds after the fact. Conversely, if native timing passes despite the static traffic disadvantage, preserve the result because it would be evidence that proof/cache/compiler effects dominate this simple traffic model; then profile those effects before writer integration.

No density, reader-speed, format, v0.29, or deferred-v0.30 claim follows from this note.
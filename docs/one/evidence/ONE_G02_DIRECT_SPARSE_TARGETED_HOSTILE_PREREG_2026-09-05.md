# ONE-G0.2 — direct sparse targeted-hostile transfer preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

The direct 16-probe sparse cold-rescue candidate can be fast only if suppressing exact proof does not introduce a brittle, public blind spot after the shared observer is silent.

This transfer test is frozen before result-bearing execution. It does not change the existing direct-sparse gate, its two-hit threshold, its 16 deterministic probe positions, or the exact relation oracle.

## Hostile construction

For each frozen source:

1. build the existing `fragmented_every96` +1 shifted relation, which is already known to create shared-observer silence in the small 4/8 KiB regime while remaining exact-proof positive;
2. compute exactly the 16 public sparse-gate probe positions `((s+1)*n)//17`, with the same boundary clamps;
3. corrupt the target byte at `probe+1`, which is the supporting location for the true +1 shift;
4. leave the remainder of the relation unchanged.

This is not a correctness attack: the exact safe dispatcher remains the oracle. The question is whether the opportunity gate can be deliberately blinded while a valid bounded relation still exists.

## Frozen envelope

Sizes: 4, 8, 16, 64 and 256 KiB.

Fresh seeds: 101, 131 and 163.

For every row report:

- exact relation enabled/disabled, best shift and proof count;
- shared-observer exact cross-object nomination count;
- whether the row actually reaches the cold-rescue stage (`shared nominations == 0`);
- sparse-gate fire/reject and compared bytes;
- exact decision produced by the sparse-gated path.

## Promotion/retirement law

The direct sparse cold-rescue shape survives this hostile transfer only if **every row that is both exact-positive and shared-observer-silent fires the sparse gate and preserves the exact best shift**.

Any shared-silent exact-positive miss retires direct sparse suppression as a generally safe cold-rescue gate in its tested deterministic form. Do not tune the threshold or move the 16 positions on this matrix after seeing the result.

Rows already caught by the shared observer are informative but do not count as cold-rescue misses, because the sparse rescue would not execute there in the intended cascade.

## Interpretation boundary

A failure does not falsify bounded shift Law discovery. It falsifies deterministic sparse suppression as a complete fallback under hostile placement. A failure should redirect research toward either evidence already fused into observation or a proof strategy whose early-exit bounds cannot be defeated by targeting a small public probe set.

No reader operation, stored-byte, decoder, v0.29, or deferred-v0.30 claim follows.
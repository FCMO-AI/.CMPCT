# ONE-G0.2 triplet block relation sketch preregistration

**Status:** frozen before hosted result.  
**Experimental version:** ONE-G0.2.

## Mission lock

The first block-cadence candidate preserved the intended architectural boundary but its hosted 24-cell falsifier did not advance after exact binding and decision-law tests passed. Independent exact-code replay indicates the bookkeeping inside each block dominates: eight probes plus local voting is still too much work for a nomination layer.

## Hypothesis

Three content-derived probes per completed 64-byte fingerprint block are enough to nominate the existing coarse add8/XOR positives while rejecting random/compressed/false-pattern controls and the prior add8->XOR fixed-grid alias. A block votes only if all three probes agree on the same non-zero relation. The same value must win across >=7/8 eligible blocks.

## Frozen causal comparison

Baseline is the existing native run+reuse observer. Candidate changes only relation nomination at block finalization. It keeps no per-byte relation histogram and no lag ring. Both arms pay input copy, FFI, forward scan, run state and FNV reuse fingerprinting.

Matrix: 64 KiB / 256 KiB / 1 MiB x the same eight structural families, 21 paired repetitions with alternating order.

## Promotion law

Advance only with exact 24-cell uniqueness; exact family-oracle decisions; identical run/reuse evidence; exactly 1.0x charged forward source scan; median wall and CPU <=1.20x baseline; no row >1.35x; and every 1 MiB row >=250 MiB/s wall and CPU.

Semantic divergence is `INVALIDATE_TRIPLET_RELATION_SKETCH`; correct semantics plus compute miss is `HOLD_TRIPLET_RELATION_SKETCH`. No post-result threshold changes.

## Non-claims

Advance would establish only a cheap coarse nomination substrate. Exact relation-span proof, final bytes eliminated per CPU second, sparse/late/phase transfer, memory traffic, selective access, authentication and Genesis supersession remain separate gates.

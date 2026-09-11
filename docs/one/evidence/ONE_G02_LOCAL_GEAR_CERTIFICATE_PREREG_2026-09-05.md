# ONE-G0.2 local Gear certificate repair — preregistration

**Status:** frozen before result-bearing execution  
**Experimental line:** `ONE-G0.2`  
**Parent evidence:** shared-observer relation nomination at `f90aaf1ee6bfef024aea7b2a8c5d9c970c87ec81`  
**Question:** can one tiny content-local witness class, derived from the same Gear table and maintained in the fused byte pass, close the shared-observer small-root miss without recreating a second relation index?

## Mission lock

The generator-distinct shared-observer validation rejected source identity alone because one required 4 KiB `damage_quarter` positive had no cross-object exact-reuse witness, even though the exact safe relation proof accepted it. The same validation produced zero false nominations and did recover the fixed-band hostile construction. This is therefore a narrow evidence-class hole, not permission to replace ONE with a relation-specific index.

The Builder adds a **local Gear certificate** only:

- a 32-byte rolling buzhash built from the already-canonical Gear byte table;
- the eight lowest distinct source-window hashes plus 32-bit source positions;
- a target-side rolling 32-byte window that checks those eight source witnesses while the existing fused byte observation pass is already reading the target;
- exact 32-byte equality is required before the certificate may nominate the pair for the existing sparse falsifier + exact safe relation proof.

No reader-visible operation changes. The certificate does not prove a relation and cannot affect reconstruction correctness. It only decides whether an already-existing exact proof is worth attempting.

## Charged state and work

Modeled incremental native state is **136 bytes**: eight `(u64 hash, u32 position)` source entries = 96 B, one 32-byte target rolling window = 32 B, and one u64 rolling hash = 8 B. Alignment/padding beyond this model must be reported by any later native implementation rather than gifted away.

Every target rolling-window update is charged. Certificate exact-window comparisons are charged. Any false nomination is charged as a downstream exact-proof attempt. Python elapsed time is explicitly not product-speed authority; this experiment is structural nomination evidence only.

## Frozen generator matrix

Sizes: **4, 8, 16, 64 and 256 KiB**.  
Seeds: **5, 23 and 47**, distinct from the rejected shared-observer validation.

Per size/seed:

1. ordinary `+1` shift;
2. quarter-damaged `+1` shift;
3. fragmented `+1` shift with one mutation every 96 bytes;
4. the existing four-edit fixed-band hostile positive;
5. a **certificate-targeted** positive that mutates one byte inside every source bottom-8 certificate window after shifting;
6. fragmented-every-32 control;
7. independent-random control.

The existing safe relation dispatcher remains the oracle for whether the relation is economically accepted. The nominator under test is the OR of:

- cross-object exact-reuse evidence already emitted by the promoted Gear observer; and
- the new local Gear certificate exact-window witness.

The certificate-targeted case is intentionally adversarial. It asks whether the two evidence classes actually complement one another rather than merely succeeding on the same easy windows.

## Frozen decision law

Advance this **hybrid evidence class** only if all of the following hold:

- every exact-proof-positive row in the frozen matrix is nominated by the hybrid;
- no exact-proof-negative row is nominated by the hybrid;
- the previously missed 4 KiB quarter-damaged regime is recovered on every fresh seed;
- the 4/8 KiB fragmented-every-96 opportunity debt is recovered on every fresh seed;
- every fixed-band-hostile positive is recovered;
- every certificate-targeted positive is recovered by the hybrid, demonstrating that the two evidence classes are not identical;
- incremental modeled state remains 136 B and no extra source scan or reader discovery is introduced.

If any required positive is missed, retire this exact bottom-8/32-byte certificate shape rather than tuning `K`, window width, seeds or thresholds on the observed result. A superseding experiment must freeze a new evidence class or new carrying-cost argument.

If false nominations appear, preserve their exact regime and proof debt. Do not silently relax the zero-false frozen gate.

## Claim boundary

A pass would establish only that a tiny content-local Gear certificate can complement existing shared-observer identity across this generator-distinct structural envelope. It would **not** establish product speed, full relation-discovery completeness, stored-byte superiority, reader performance, release readiness, or superiority over v0.29/deferred-v0.30. Native fused-pass timing and memory traffic remain separately payable debt.
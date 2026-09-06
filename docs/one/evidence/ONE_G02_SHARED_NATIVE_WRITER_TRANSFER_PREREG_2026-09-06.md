# ONE-G0.2 shared native writer transfer — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission Lock / falsifiable hypothesis

Repository evidence has promoted direct final-buffer canonical emission as the preferred research-writer shape, while V3 showed that consuming the native Segment buffer directly removes real per-segment materialization/assembly work but failed its frozen breadth gate (10 mature productive rows <=0.95x, 12 required).

The next system-scope step is not another Python serializer micro-tune. Test whether transferring the same single ONE representation into a shared native writer boundary removes enough Python object/list/tuple/bytearray traffic to make the direct native-buffer principle broad rather than workload-shaped.

Hypothesis: compared with the promoted plan-direct V2 writer, a native ONE0 writer that consumes the same admission result and exact native one-pass Segment buffer and performs bounded validation plus final canonical emission in native code will materially reduce whole charged writer elapsed while producing byte-identical ONE0 and preserving every reader/resource semantic.

Disproof: any semantic/oracle/wire mismatch, malformed-buffer acceptance, resource-bound weakening, or failure of the frozen broad performance gate below retires this transfer shape. Do not rescue a failure by workload, size, segment count, Surprise density, or post-hoc dispatch.

## Frozen arms

Baseline: promoted root-hash-charged plan-direct V2 writer path:

`root hashes -> admission -> native one-pass segmentation -> Python plan/direct ONE0 writer`

Candidate:

`root hashes -> admission -> native one-pass segmentation -> shared native bounded ONE0 writer`

Both arms use identical source/target bytes, root identities, admission function, native Segment producer, relation enable decision, ONE limits, root ordering, node/ref semantics, and final wire grammar. The candidate may remove language/runtime staging only; it may not change the representation.

## Required semantic / hostile gates

- canonical wire bytes byte-identical to V2 on every measured row;
- WireStats-equivalent total/Surprise/control bytes exact;
- decoded roots reconstruct `previous` and `current` exactly;
- independent native Segment plan oracle exact;
- same relation enable/best-shift/exact-proof facts;
- reject zero-length segments, source refs outside the previous root, Surprise spans outside the target, unknown kinds, incomplete/over coverage, invalid segment count and node-count/resource overflow;
- no new reader opcode and no weakened integrity, locality, recovery or portability semantic.

## Frozen workload / timing method

Reuse the V2/V3 frozen temporal matrix, sizes, productive/control membership and independent oracle. Mature rows are >=16 KiB. Use 31 rounds with alternating A/B-B/A ordering and GC disabled during paired timing. Root SHA-256 computation, admission, segmentation, validation and final writer call are inside each timed arm.

Record canonical stored bytes, Surprise bytes, writer elapsed, segment count, reader work/materialization and candidate native allocation capacity/actual final bytes. Stored bytes must remain exactly 1.0x because this is a writer-transfer hypothesis, not a density claim.

## Frozen promotion gate

On mature rows:

- semantic failures = 0 and oracle failures = 0;
- malformed native-buffer probes pass;
- productive median candidate/baseline <= **0.80x**;
- at least **15** mature productive rows <= **0.90x**;
- no mature productive row > **1.03x**;
- mature control median <= **1.03x**;
- no mature control row > **1.08x**.

The stronger median/breadth requirements are deliberate: moving a boundary into native code adds implementation and portability burden, so marginal speed is insufficient.

## Claim boundary

If promoted: shared-native research-writer transfer for the frozen adjacent-version envelope only. No arbitrary/fused-discovery, filesystem/product, authenticated-placement, RSS/native-peak, v0.29/v0.30 or 15-workload Genesis authority is granted.

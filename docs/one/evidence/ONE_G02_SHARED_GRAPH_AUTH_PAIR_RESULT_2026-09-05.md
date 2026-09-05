# ONE-G0.2 shared stored-graph authentication — edited pair result

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `67ac7c850dbbb4b30da1a6821d4704f116158e39`  
**Workflow:** `33952318397`  
**Job:** `101269291652`  
**Artifact:** `9965232671`  
**Artifact digest:** `sha256:d08b269e7284cac2be8020524739bd49d72e753a13fb0653ac3411a56a267a6e`  
**Decision:** `advance_shared_stored_graph_auth_boundary`

## Mission lock

The isolated reconstructed-root authentication experiments found no standard 32-byte Merkle leaf/fanout geometry inside the frozen <=3.5% local integrity-index / <=1.20x median 4 KiB authenticated-touch rectangle. The commitment-width diagnostic further showed that the same fixed-partition tree family would need hypothetical commitments around 20 bytes before entering that rectangle.

Rather than weaken SHA-256 integrity, this Builder changed the cost boundary in the ONE-native way: authenticate the information that is actually stored. For an edited temporal pair, ONE stores the basis once and represents the second root as one translation Law plus explicit Surprise. The experiment therefore asks whether a much finer authenticated basis can be paid for by the bytes eliminated through Law sharing.

No old codec or reader-visible temporal opcode was introduced.

## Frozen representation and test

The corpus is the existing 64 edited-version rows: 64 KiB and 256 KiB bases, eight independent bases at each size, and 1/4/16/64 mutations.

The charged candidate stores:

- one literal basis;
- every non-root SHA-256 hash in the basis authentication tree;
- a fully stored generic graph manifest containing the basis-tree root, Law control, Surprise length/digest and leaf geometry;
- the complete deterministic Surprise wire (`ULEB count`, then `ULEB position delta + literal byte` per mutation).

The graph-root SHA-256 replaces the already-required root digest rather than being double counted. On a selective read, the reader touches and authenticates the complete small manifest and Surprise blob plus exactly the basis leaves and Merkle siblings needed by the 4 KiB range. Starts sweep **every byte offset modulo the leaf**, not a favorable alignment subset.

The density comparator is deliberately conservative: two completely unauthenticated literal roots, so the candidate receives no baseline-integrity credit.

A leaf advances only if, on every tested row:

1. complete persisted candidate bytes are strictly below the two literal roots;
2. median authenticated touch amplification is <=1.20x;
3. every reconstructed range is exact;
4. basis-payload, Surprise and manifest corruption are all rejected.

## Result

All **704 representation rows** (64 temporal rows x 11 leaf sizes) completed with **zero reconstruction failures and zero corruption-test failures**.

Four leaf sizes pass the frozen global gate: **80, 96, 112 and 192 bytes**.

| Leaf | Worst candidate fraction of two literals | Worst row median touch | Worst alignment touch | Interpretation |
|---:|---:|---:|---:|---|
| 80 B | 90.3267% | 1.1560x | 1.2224x | passes median gate; ~9.7% complete saving |
| 96 B | 83.6617% | 1.1716x | **1.1716x** | passes; ~16.3% complete saving |
| 112 B | **78.9497%** | **1.1873x** | **1.1873x** | strongest all-alignment point; ~21.1% complete saving |
| 192 B | **66.9868%** | **1.1716x** | 1.2185x | best density among passers; median-local, some hostile alignments >1.20x |

The 112-byte point is the strongest current balanced result because it exceeds the frozen median requirement and, additionally, every tested byte alignment remains below 1.20x. Even in its worst row the **entire authenticated ONE representation is 21.05% smaller than two literal roots** while every 4 KiB selective read remains at or below **1.187255859375x** authenticated traffic.

The 192-byte point demonstrates a deeper density/access continuum: the complete pair is at most **66.9868469%** of two literal roots (~33.0% saving) while the worst row median remains **1.171630859375x**, but its worst individual alignment reaches **1.218505859375x** and remains explicit debt if a hard per-request 1.20x contract is later required.

The neighboring losses matter. A 64-byte basis leaf nearly reaches raw-pair size (`100.18997%` worst) and therefore fails density despite good access. 128-byte and larger ordinary points save more bytes but breach the frozen median access target until the 192-byte geometry's alignment distribution happens to recover the median criterion. Nothing was post-hoc removed from the leaf grid.

## Causal interpretation

This result rehabilitates the earlier Merkle negative by changing **what pays for authentication**, not by weakening authentication.

A reconstructed-root view asks every logical version to independently afford a fine-grained integrity index. ONE's stored-information view instead spends a relatively large tree on one shared basis and then reuses that authenticated information through deterministic Law execution. The Law's eliminated second-root bytes are large enough to pay the integrity sidecar while still leaving a net complete-byte saving.

That is exactly the architectural leverage ONE is supposed to create: global Law sharing can finance local Crystallization that would look too expensive in isolation.

The result does not prove that 112-byte Merkle leaves are a final format choice. It proves the **boundary** is viable.

## Strongest self-critique / exported debt

The winning fine leaves create substantial encoder hash work. For example, a 112-byte binary basis tree requires hundreds to thousands of leaf/parent hash operations per root. That work was not measured as product-speed evidence here. The candidate also assumes a compact generic graph manifest, reads the complete small Surprise blob on every derived selective read, and has only been tested on two-root edited families.

Open debt therefore includes:

- creation hashing CPU, elapsed time and memory traffic;
- SIMD/batched or otherwise fused tree construction;
- larger version families and changed-cone update invalidation;
- physical wire/index seeking rather than in-memory proof objects;
- generic Law + Surprise + Crystal manifest encoding;
- failure blast radius and recovery behavior;
- incompressible/surprise-dense cases where Law should lose MDL admission rather than force this representation.

Correctness and integrity remain hard: all tested basis, Surprise and manifest corruptions were rejected.

## Decision and next experiment

**Advance the stored-information authentication boundary.** Do not promote a leaf size yet.

The next decisive experiment must profile the creation-side hash work of the passing 80/96/112/192-byte points and test whether batching/fusion can make their marginal information yield credible. The gain-retention gate is the complete-byte/access result above: speed work may not optimize away the authenticated sharing that produced it.

A parallel structural transfer should extend the same graph authentication model from one edited pair to a multi-version family, where shared-basis amortization is expected to increase but update/failure-blast costs also become more important.

## Comparator / claim boundary

The literal-pair baseline in this experiment is **not** frozen v0.29 or deferred v0.30. No CMPCT1 supremacy claim follows from this result, and the September 11 15-workload comparison remains untouched. This is mechanism-level ONE evidence showing that authenticated selective Crystallization can coexist with Law+Surprise density on the tested temporal shape.

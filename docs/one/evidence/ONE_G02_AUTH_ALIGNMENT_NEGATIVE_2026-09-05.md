# ONE-G0.2 authenticated-range alignment transfer — scoped negative

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `f89314a960f0690e099585cdb2a95881009f01bc`  
**Workflow:** `33951755283`  
**Job:** `101267749854`  
**Artifact:** `9965047717`  
**Artifact digest:** `sha256:1d005b6c446e893e83775aa73ebc7c7e363f5820953bf2b9cbc212cdc6bae3d1`  
**Decision:** `reject_fixed_reconstructed_root_leaf_knee_for_arbitrary_alignment`

## Mission lock

The preceding generic authenticated-range Pareto used a centered 4 KiB request. Its 2 KiB leaf candidate met the frozen density/access target at 64 KiB and 256 KiB roots, but that request was exactly aligned to 2 KiB leaf boundaries. The missing transfer question was whether the same fixed reconstructed-root Merkle layout remains viable for arbitrary byte-range alignment.

The transfer experiment preserved the prior root sizes, request length, leaf grid, integrity accounting and thresholds. Only request alignment changed. Starts sweep every 64 bytes modulo each leaf plus the hostile `leaf_bytes - 1` offset. Every proof is independently verified against the exact requested bytes.

Frozen transfer target at both 64 KiB and 256 KiB roots:

- persistent integrity-index overhead <= 3.5% of root bytes;
- median authenticated bytes touched <= 1.20x requested bytes;
- every proof verifies exactly.

No post-result alignment filtering, leaf-grid expansion or threshold search was allowed.

## Exact result

All semantic tests and every authenticated proof completed successfully on the exact source above. No leaf size in the frozen grid satisfies both density and arbitrary-alignment access targets.

| Leaf | 64 KiB index | 64 KiB median touch | 256 KiB index | 256 KiB median touch | Decision |
|---:|---:|---:|---:|---:|---|
| 1 KiB | 6.1584% | 1.3125x | 6.2271% | 1.34375x | density fails |
| 2 KiB | 3.0334% | 1.5546875x | 3.1021% | 1.5859375x | access fails |
| 4 KiB | 1.4709% | 2.046875x | 1.5396% | 2.078125x | access fails |
| 8 KiB | 0.6897% | 2.0234375x | 0.7584% | 2.0390625x | access fails |
| 16 KiB | 0.2991% | 4.015625x | 0.3677% | 4.03125x | access fails |

The 2 KiB candidate is the clearest falsification: its persistent index remains within the frozen 3.5% density budget, but arbitrary alignment raises median authenticated traffic from the favorable aligned case (~1.06-1.09x) to **1.5546875x at 64 KiB** and **1.5859375x at 256 KiB**.

The 1 KiB leaf moves traffic in the desired direction but still misses the access target and pays more than 6% persistent integrity overhead. Larger leaves reduce index bytes while making complete-leaf authentication increasingly expensive.

## Causal interpretation

The earlier feasible knee was an alignment artifact. With fixed authenticated leaves, a request that begins inside a leaf must authenticate complete intersecting leaf payloads. For a 4 KiB request and 2 KiB leaves, most nonzero alignments span three leaves rather than two. The extra complete leaf dominates proof hashes, so the cost is structural rather than an implementation micro-optimization.

This result does **not** falsify generic range-cone execution. The generic ONE range evaluator already showed that Law execution itself can remain source-size-independent at 2x modeled materialization/work. The negative applies specifically to **fixed Merkle leaves over each reconstructed logical root** as the integrity/addressability mechanism under the current density/access target.

## Scoped negative constraint

Do not promote the 2 KiB reconstructed-root leaf size as a generic authenticated selective-read solution. Do not reopen the same fixed-leaf family merely by tuning leaf size, alignment or thresholds on this corpus.

Reopening requires a causally different representation that reduces complete-leaf overfetch or amortizes authentication state across shared stored information. Candidate directions include:

1. authenticate the stored Law + Surprise / Crystal information graph rather than independently Merkleizing every reconstructed root;
2. use smaller authenticated sub-leaf units whose hash/index state is shared or compressed rather than paid independently per logical root;
3. derive authenticated output ranges from already-authenticated stored graph objects so exact deterministic Law execution carries trust without whole-root materialization.

Any successor must charge all persisted hashes/index/control bytes, proof traffic, complete payload bytes that must be read for verification, creation hashing cost, update invalidation and failure blast radius. Integrity remains non-borrowable.

## Claim boundary

This is ONE research evidence about integrity/access economics. It changes no canonical wire format, reader ontology, release authority or v0.29/v0.30 comparison. It does not establish product read speed because physical wire seeking/index integration remains unresolved.

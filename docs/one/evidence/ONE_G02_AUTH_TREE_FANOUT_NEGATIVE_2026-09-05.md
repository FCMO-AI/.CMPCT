# ONE-G0.2 fixed-partition authenticated-tree fanout Pareto — negative

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `032d7865df4473916b992a75011f352bce204e3a`  
**Workflow:** `33951933310`  
**Job:** `101268246450`  
**Artifact:** `9965098550`  
**Artifact digest:** `sha256:97ad1cf962d6e9cb2c3af410c0968677b1b94523b6ed05262c4bedaa4c856c75`  
**Decision:** `retire_fixed_partition_tree_fanout_tuning`

## Question

The arbitrary-alignment experiment falsified the original binary fixed-leaf knee. Before changing the integrity representation boundary, this experiment tested whether tree fanout itself could recover the density/access target by reducing internal-level storage enough to permit finer authenticated leaves.

The frozen practical grid exhausts:

- roots: 65,536 and 262,144 bytes;
- request: 4,096 bytes;
- leaf size: 256 through 4,096 bytes in 64-byte increments;
- fanout: 2, 4, 8, 16, 32, 64, 128, 256;
- arbitrary alignment: every 64 bytes modulo leaf plus `leaf_bytes - 1`;
- SHA-256-sized 32-byte commitments;
- every non-root node hash persisted, including leaves;
- every sibling commitment and complete intersecting leaf payload charged on reads.

The frozen target remains <=3.5% persistent integrity index and <=1.20x median authenticated bytes touched at both root sizes. Binary 2 KiB anchors were required to reproduce the preceding exact geometry before the larger grid could be interpreted.

## Result

The binary parity anchors matched exactly. **No point in the full fanout/leaf grid met the frozen target.**

The nearest overall point was fanout 4 with 1,216-byte leaves:

- 64 KiB root: index **3.5217285%**, median touch **1.2578125x**, max **1.546875x**;
- 256 KiB root: index **3.5171509%**, median touch **1.28125x**, max **1.5703125x**.

That point misses both target dimensions: index is slightly above 3.5%, while median authenticated traffic is materially above 1.20x. Moving to 1,664-byte leaves lowers index to ~2.58% but raises median traffic to **1.2890625x** at both root sizes. Increasing fanout does not remove the tradeoff because it saves some internal hashes while increasing sibling commitments exposed by range proofs.

## Causal interpretation

This closes the obvious tree-shape escape hatch. Under 32-byte commitments, fixed partitioning has two coupled costs:

1. finer leaves reduce complete-payload overfetch but require many persisted leaf commitments;
2. larger fanout removes tree levels but exposes more sibling commitments in proofs.

Within the broad frozen grid, those costs do not cross inside the required density/access rectangle. The failure is therefore not specific to binary trees or to the earlier 1/2/4/8/16 KiB leaf ladder.

## Scoped negative constraint

Do not continue tuning fixed reconstructed-root Merkle leaf size or fanout under the same 32-byte commitment accounting merely to search for a narrow benchmark green. Reopening this family requires a causally different fact, such as materially smaller admissible commitments with an explicit security argument, shared/compressed authentication state, or a different representation boundary that authenticates stored Law/Surprise/Crystal information rather than each reconstructed output independently.

The next diagnostic may ask how much commitment width would have to shrink before the same fixed-partition geometry becomes feasible. That is an economics boundary only: reducing SHA-256-sized authentication is **not** automatically admissible, because integrity/security is non-borrowable.

## Claim boundary

This is research evidence about authenticated selective-access economics. It changes no canonical wire format, reader vocabulary, product integrity guarantee, v0.29/v0.30 comparator result or release authority.

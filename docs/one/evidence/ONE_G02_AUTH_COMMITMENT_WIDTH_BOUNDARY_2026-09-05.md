# ONE-G0.2 authentication commitment-width boundary

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `2afadfdcc59435c2784c2db64135e66d5b6fce46`  
**Workflow:** `33952069898`  
**Job:** `101268616369`  
**Artifact:** `9965140210`  
**Artifact digest:** `sha256:988511349cd0cc1393a796abf9bec8047f13f8af61a2a5ddde052f0b12741666`  
**Decision:** `fixed_partition_requires_sub_sha256_commitments`

## Question

After fixed binary leaves and then a broad fixed-partition fanout grid failed the arbitrary-alignment density/access target with 32-byte commitments, this experiment measured the commitment-byte economics directly. It did **not** propose weaker integrity as a solution.

The exact leaf/fanout/alignment grid was retained. Only the hypothetical commitment width was varied across 32, 28, 24, 20 and 16 bytes. Every non-root node commitment remained persisted, every proof sibling remained charged, and complete intersecting leaf payloads remained charged.

The target remained <=3.5% persistent index and <=1.20x median authenticated bytes touched at both 64 KiB and 256 KiB roots.

## Result

| Commitment | Feasible geometries | Best/nearest frozen point |
|---:|---:|---|
| 32 B | 0 | fanout 4 / 1,216 B leaves; misses both index and access |
| 28 B | 0 | fanout 2 / 1,664 B leaves; access still >1.25x |
| 24 B | 0 | fanout 4 / 960 B leaves; 1.2246x / 1.2422x median access |
| 20 B | **1** | fanout 8 / 768 B leaves |
| 16 B | 6 | multiple points |

The largest hypothetical width that enters the frozen target is **20 bytes**. Its unique feasible point is fanout 8 / 768-byte leaves:

- 64 KiB root: index **3.02734375%**, median authenticated touch **1.173828125x**, max **1.3564453125x**;
- 256 KiB root: index **2.98461914%**, median authenticated touch **1.193359375x**, max **1.3759765625x**.

At 24 bytes the nearest point remains outside the target: fanout 4 / 960-byte leaves gives **3.44848633% / 1.224609375x** at 64 KiB and **3.37066650% / 1.2421875x** at 256 KiB. Thus the boundary is not a tiny 32->28-byte accounting correction; this tree family needs commitments materially shorter than the current SHA-256-sized 32-byte identity to cross the chosen Pareto rectangle.

## Security / integrity boundary

This experiment grants **zero** authority to truncate SHA-256 or otherwise weaken CMPCT integrity. A shorter digest changes collision/second-preimage/security economics and would require a separate cryptographic threat model, security analysis, hostile review and hardening decision. Correctness and authentication are non-borrowable under CMPCT doctrine.

The value of the result is diagnostic: it quantifies the missing resource. Under the tested standard fixed-partition Merkle family, approximately 20-byte commitments are needed before density and arbitrary-alignment access can coexist at the frozen target. If the project wishes to retain 32-byte commitments—and absent a security case it should—the representation must instead reduce the **number of independently paid commitments/proof siblings** or move authentication to a different information boundary.

## Next architectural implication

The strongest next direction is not another leaf threshold. It is to authenticate the stored ONE information graph—Law, Surprise regions and Crystals—so authentication state can be shared across multiple derived roots and deterministic Law execution can carry trusted information into output ranges. A second possible direction is a proof/commitment structure whose proof size is decoupled from Merkle sibling count, but such a primitive must pay creation CPU, reader complexity, portability and cryptographic assurance.

## Claim boundary

This is research cost-model evidence only. It changes no canonical wire format, hash policy, reader ontology, v0.29/v0.30 comparator result, product security claim or release authority.

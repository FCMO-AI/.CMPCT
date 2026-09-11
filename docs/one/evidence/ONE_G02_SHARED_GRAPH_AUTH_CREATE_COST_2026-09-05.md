# ONE-G0.2 shared graph authentication — creation-cost audit

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `514c3085050050b23e7e4e7c4418610a38f522ef`  
**Workflow:** `33952455805`  
**Artifact:** `9965261047`  
**Artifact digest:** `sha256:11a18bc644dff4474bebd195aa762482d23ebc2eb75dc642c6bb7aa370183d78`  
**Decision:** `creation_hashing_rehabilitation_required`

The preceding shared stored-graph experiment advanced 80/96/112/192-byte authentication leaves on complete density + selective-access evidence. This audit preserves those leaves and measures the creation bill rather than treating read locality as sufficient.

The hosted elapsed comparison uses the exact Python `AuthTree` implementation versus one whole-root `hashlib.sha256` over identical deterministic random inputs, with two warmups and 15 timed repetitions. It is diagnostic rather than native authority. In parallel, an implementation-independent counter charges the exact SHA-256 grammar: every leaf hash, every binary parent hash and the final root commitment, plus every byte presented to SHA-256.

| Root | Leaf | Hosted elapsed / whole SHA | SHA calls | SHA input / source |
|---:|---:|---:|---:|---:|
| 64 KiB | 80 B | 38.75x | 1,644 | 2.2053x |
| 64 KiB | 96 B | 32.18x | 1,371 | 2.0058x |
| 64 KiB | **112 B** | **28.10x** | **1,178** | **1.8648x** |
| 64 KiB | 192 B | 16.80x | 688 | 1.5051x |
| 256 KiB | 80 B | 39.26x | 6,560 | 2.2017x |
| 256 KiB | 96 B | 32.58x | 5,468 | 2.0017x |
| 256 KiB | **112 B** | **28.90x** | **4,690** | **1.8595x** |
| 256 KiB | 192 B | 17.15x | 2,737 | 1.5016x |

Every row meets the preregistered material-debt condition. The 112-byte balanced point therefore exports a real structural bill: even an ideal removal of Python overhead cannot erase the approximately **1.86x SHA input traffic** or thousands of independent hash nodes implied by the current binary tree.

This does **not** invalidate the prior complete-byte/access win. Breakthrough Rehabilitation applies: preserve the demonstrated ability of shared Law to finance authenticated fine-grained access, then attack the exported creation debt rather than making leaves coarse enough to tune the gain away.

The next speed Builder should use an exact-root native implementation and test level-batched/multi-buffer hashing or a similarly fused construction. Promotion requires byte-identical roots and proofs; no alternative hash/security primitive may be substituted merely for speed. The hosted 28-39x ratios are not product-speed claims, but they make native profiling mandatory.

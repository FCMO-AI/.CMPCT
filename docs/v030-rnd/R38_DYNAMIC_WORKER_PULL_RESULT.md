# R38 persistent dynamic worker-pull candidate encoding — result

Status: **POSITIVE MECHANISM RESULT; PRODUCT VALIDATION REQUIRED**  
Decision: `DYNAMIC_PULL_TRANSFERS`  
Evidence head: `34d18732736be042c6ae3d050026cf5252d8502c`  
Workflow run: `35213928013`  
Result-bearing job: `105177769523`  
Artifact: `10493133182`  
Artifact ZIP SHA-256: `77c5346c2f7e603a8e053d0943036f8be8a3a8bba4f6e564608d107165a48434`

## What was tested

R38 followed R36's localization of excess per-candidate scheduling waits and R37's negative showing that static equal-count batching destroys useful load balancing. It held `_encode_candidate`, prepared Builder state, sorted-hash candidate order and worker count fixed, changing only execution ownership: inherited one Future per candidate versus exactly W long-lived workers that dynamically claim canonical indices and write into a preallocated canonical-order result vector.

The preregistration was frozen before execution. Exact encoded tuple identity was mandatory. Both `full-backups` and `nested-only` had to save at least 2 ms median over 9 alternating repetitions.

## Result

Exact encoded identity passed throughout.

| Target | Candidates | Itemwise median | Dynamic-pull median | Pull/itemwise | Median saved |
|---|---:|---:|---:|---:|---:|
| full-backups | 231 | 0.205220 s | 0.198662 s | **0.968045x** | **+0.006558 s** |
| nested-only | 194 | 0.172903 s | 0.159141 s | **0.920406x** | **+0.013762 s** |

Thus the frozen decision is `DYNAMIC_PULL_TRANSFERS`. The mechanism recovered the transfer that R37 lost: it reduced Future ownership from O(N) to O(W) without statically assigning an expensive tail to one worker.

## Interpretation

This is evidence that canonical output order and execution ownership should be decoupled. CMPCT does not need one Future per candidate to remain deterministic, and it does not need static batches to reduce scheduler overhead. A small persistent worker set can dynamically balance candidate cost while materializing results by canonical index.

The measured effect is meaningful but not yet product credit: about 3.2% candidate-phase improvement on full-backups and 8.0% on nested-only on this runner. The full target's absolute gain is only ~6.6 ms, so whole-build validation may dilute it; that is the strongest immediate risk.

## Product authorization and next gate

R38 authorizes a minimal Builder implementation of this exact scheduling structure, with no codec/admission/format changes. The next evidence must be uninstrumented and compare complete builds from identical sources. It must prove complete archive-byte identity and repeated end-to-end create improvement, then account for CPU, RSS and I/O before any runtime/release claim.

If whole-build improvement does not clear the repository's timing-noise rules, preserve R38 as mechanism evidence but do not productize it merely because the candidate phase improved.

## Product credit

None yet. R38 is research/mechanism evidence only.
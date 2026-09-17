# R37 deterministic batched candidate encoding — result

Status: **DECISIVE NEGATIVE FOR NAIVE EQUAL-COUNT CONTIGUOUS BATCHING**  
Decision: `BATCHING_DOES_NOT_TRANSFER`  
Evidence head: `774248e58923dd31d4d6d601088a8b530e1a0110`  
Workflow run: `35209397229`  
Result-bearing job: `105163031437`  
Artifact: `10491433048`  
Artifact ZIP SHA-256: `d19dd3da6be207e43710cba6268b8fb057f75dcabc20419f180400243ba1d47d`

## What was tested

R36 had localized transferable excess `Condition.wait` time to `Builder.build` at the per-candidate `ThreadPoolExecutor.map` materialization boundary. R37 held `_encode_candidate`, worker count, prepared Builder state, sorted-hash candidate order and encoded output fixed, changing only scheduling granularity from one executor item per candidate to at most one equal-count contiguous slice per worker.

The frozen preregistration required exact encoded-tuple identity and strictly positive median time saved on **both** frozen `full-backups` and `nested-only` targets. Seven alternating measured repetitions per arm followed a warm identity pass.

## Result

Exact encoded identity passed on every measured arm/repetition, so the timing comparison is semantically clean.

| Target | Candidates | Itemwise median | Batched median | Batched/itemwise | Median saved |
|---|---:|---:|---:|---:|---:|
| full-backups | 231 | 0.175800 s | 0.199905 s | **1.137118x** | **-0.024105 s** |
| nested-only | 194 | 0.142863 s | 0.131847 s | **0.922892x** | **+0.011016 s** |

The nested target improved by about 7.71%, consistent with R36 showing real scheduler/wait overhead there. But full-backups regressed by about 13.71%, a larger absolute loss. The preregistered transfer condition therefore fails.

## Interpretation

Do **not** productize naive equal-count contiguous batching. R36's wait-owner localization remains valid, but R37 shows that simply collapsing 194–231 candidate futures into eight equal-count contiguous futures exports enough lost load balancing / tail utilization to erase the scheduler win on the full target.

This is useful negative evidence: the next intervention must preserve coarse-grained scheduling benefits **without** forcing one worker to own an unlucky expensive tail. The stronger next question is whether canonical output order can be decoupled from execution ownership entirely: assign indexed candidates deterministically to a small number of cost-balanced worker batches, let each batch return `(canonical_index, encoded_row)` pairs, then materialize into a preallocated canonical-order result vector. A cheap cost proxy can be derived from information already used by `_encode_candidate` before compression (raw length, early-return Deflate ownership, number of Zstd levels, dictionary eligibility and WAV extra-codec work), avoiding workload identity and result-driven tuning. This class is **not authorized merely by R37**; it needs a new falsifiable test showing that the proxy actually controls tail imbalance while retaining the scheduler reduction.

Do not respond by sweeping worker counts, chunk counts, or result-driven batch sizes. The equal-count/W-contiguous-batch family is retired as the immediate product move.

## Product credit

None. No product code changed and no release/runtime claim is earned. The strongest new project truth is a narrowed mechanism: per-candidate scheduling has measurable overhead, but naive maximal coarsening is not generally transferable because scheduling granularity and load balance are coupled.

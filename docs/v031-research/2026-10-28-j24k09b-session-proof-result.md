# J24K09b — Fully charged VZIP session-proof ownership oracle result

Date: 2026-10-28 UTC  
Status: **SCIENTIFIC DECISION — amortized proof wins for repeated reads, but is NOT yet a safe mutable-source product cache.**  
Prospective [preregistration](2026-10-28-j24k09b-session-proof-ownership-prereg.md) committed at `724bb53cbc63ffb9e63c2f16b961fb7938413e6e` **before** instrument commit `a9452b6437fbded32a1adaa3c5c57245b9a4ebf3`.  
Hosted source head: `674fb910970069178929a9251cdeda7ef7f476cd`; [three-host scientific workflow #40642559867](https://github.com/FCMO-AI/.CMPCT/actions/runs/40642559867).  
No product promotion/release/version/format claim.

## Test and controls
Same synthetic physical archive bytes, same process and `range_vzip` primitive. At 64, 512 and 4096 preceding STORED streams, compare Q=1/8/64 repeated one-byte suffix queries:
- **Current correct candidate:** re-parse real BHDR for all skipped physical streams on *every* query.
- **Fully charged snapshot oracle:** call the exact same BHDR validator on **every physical stream before** the first query, store its sizes as a new per-session array, then use that proven local array for all queries. Count the full prevalidation scan, array allocation and all Q reads in wall/CPU time.
- **Unsafe lower bound:** no physical size proof, zero product credit.
Five ABBA cycles yield ten raw measured sessions per safe alternative and five unsafe lower-bound sessions per matrix cell; all requests verify exact original suffix content. Windows CPU timers may quantize; raw samples are retained. Memory charge includes Python array plus integer objects (2,360 B for 64, 18,552 B for 512 and **147,736 B for 4096**), not entire Reader/process RSS.

## Direct measured medians: total session wall, 4096 streams
| Host | Q | Physical proof per query | Prevalidated-once oracle | Speedup of oracle |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 | 1 | 5.877 ms | 6.745 ms | 0.87x (loss) |
| Ubuntu 24.04 | 8 | 46.962 ms | 14.598 ms | **3.22x** |
| Ubuntu 24.04 | 64 | 374.684 ms | 77.367 ms | **4.84x** |
| macOS 14 | 1 | 3.835 ms | 4.436 ms | 0.86x (loss) |
| macOS 14 | 8 | 34.720 ms | 10.638 ms | **3.26x** |
| macOS 14 | 64 | 252.205 ms | 52.652 ms | **4.79x** |
| Windows 2022 | 1 | 6.838 ms | 8.018 ms | 0.85x (loss) |
| Windows 2022 | 8 | 54.739 ms | 16.890 ms | **3.24x** |
| Windows 2022 | 64 | 435.133 ms | 89.145 ms | **4.88x** |

The other six matrix cells per host (64 and 512 streams, same Q values) show the same qualitative split: at Q=1 the once-only owner loses ~13–15%; at Q=8 it wins 3.17–3.33x, and at Q=64 wins 4.76–5.11x. This held across 27 matched host/size/query cells, with all 9 within-host rows per platform retained in exact-workflow raw stdout/artefacts. Observed crossover lies between Q=1 and Q=8 for these synthetic workloads. It is **not** a guaranteed workload-independent crossover.

## Decision and strongest counterargument
The dominant cost is **repeated metadata/BHDR proof per prior stream**, not payload reconstruction. Prevalidation changes the ownership boundary and has material information-economy headroom for repeated reads. However, a cached prior proof is not automatically valid after concurrent **same-inode physical modifications**: FD ownership of a path is not immutable byte snapshot custody. A feature that caches verified geometry with no coherency protocol may recreate the very wrong-coordinate failure being repaired. This oracle was deliberately run on an unmodified synthetic in-memory snapshot. A safe product path needs either a genuinely immutable snapshot, a source mutation/epoch boundary with proven race semantics, or continued per-query physical checking. A cheap fstat timestamp cannot on its own be credited as an adversarial coherency proof.

It is **not** justified to make `read_range` silently use a per-member persistent cache after this oracle. Correctness under mutation, authenticated content, bounded RSS/reader size, real open/list/verification economics, mixed modes, extraction, platform/natives and official release gates remain unmeasured. J24K09's existing simple per-query correctness fix stays a guarded Draft candidate, with measured high-read-count debt.

## Transferable counterfactual
The initial single-read micro already showed ~5–6x cost relative to a predecoded size control. Had we measured total multi-query sessions first, the repeated-BHDR cost could have been separated immediately from any presumed fundamental inability to locate suffixes quickly. Future source-custody research should ask explicitly whether a proposed cached fact remains true under concurrent mutations before granting it product credit. This is a prospectively recognizable experimental discriminator, **not an earned change to the normative Discovery Engine policy**.

## Next dependency-safe decisive experiment
First distinguish immutable-snapshot environments from mutable live source. If a valid portable immutable-source contract/snapshot mechanism exists with bounded bytes/RSS/startup cost, test a per-recipe proof-once Reader under that contract versus repeated-BHDR Reader and full reconstruction, including invalidated-source adversaries. Otherwise retain the per-query proof as safe-within-inherited-input assumptions, narrow optional caching to explicit caller-supplied immutable lifetime, or retire the cache family without loosening integrity. Keep mode2 recompression cost and partial SHA authentication separate.

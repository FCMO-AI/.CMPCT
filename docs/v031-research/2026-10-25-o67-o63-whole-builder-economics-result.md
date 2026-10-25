# O67 — Full physical Builder economics, actual O60 vs O63

Date: 2026-10-25 UTC. Category: **hosted same-host research evidence**, NOT official release/ZIP performance or a general-compression claim.

## Immutable identities and prospective protocol
- Preregistration: `docs/v031-research/2026-10-25-o67-o63-whole-builder-economics-prereg.md` committed before test implementation (`0f7dcfc5ce782531044062a5162a5872b0dfd3be`).
- Frozen original runtime: O60 PR #415, exact commit `c88a6bc29b9ec8738e23aab788b7c09ab0390e79`, original Builder blob `bda9d7f8005e276ba891aac75ae50eabe67bd431`.
- Candidate runtime: O63 PR #418, exact commit `18e32cae012f5dca9fc47f10d194f8b81005c85c`, Builder blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`.
- Shared unchanged codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`.
- Original result-bearing research HEAD `5813a46699a1fff65069ff6555244bebe9918394`.
- **Actual hosted GitHub [Actions #40174270902](https://github.com/FCMO-AI/.CMPCT/actions/runs/40174270902) SUCCESS**, one genuinely executed Ubuntu 24.04/Python 3.11.17 job `121111472654`. Original artifact `12591332850`, ZIP SHA-256 reported by GitHub uploader `4fc69f9467a9a7fba085d80b4d94fdef417e10a9de82b00ecf39812ebd59afdc`, containing 80 raw JSON observations plus materialized archives/receipt summary.
- Two distinct non-editable installed CMPCT package environments built from actual O60 and O63 immutable Git sources, same physical input tree, five scenarios, four independent A-B-B-A blocks each, 4 fresh processes per block per shape => **80 actual observed runs**. Each test reconstructs each original file exactly and performs Reader SHA verification. All conditions executed successfully, no result-bearing skip.
- Raw observations, sample timings, CPU, peak RSS, output blocks, complete archive bytes+SHA and summary are in the original artifact, not fabricated or regenerated post-result.

## Actual measurements (medians; same runner; complete output bytes)
| Structural source | O60 archive B | O63 archive B | Exact byte effect | O60 create wall ms | O63 create wall ms | Candidate - base wall ms | Candidate - base CPU ms | Other measured effect |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Regular ZIP positive control | 4,124 | 4,124 | **0 B**, identical SHA | 3.677038 | 3.518114 | -0.158924 | -0.159003 | peak RSS median 24,582 -> 24,402 KiB |
| Early unsupported fixed-Huffman ZIP | 2,157 | 2,157 | **0 B**, identical SHA | 2.808523 | 2.820321 | **+0.011799** | **+0.011403** | small measured overhead |
| **Late unsupported fixed-Huffman ZIP** | **4,687** | **2,157** | **-2,530 B (-54.0%)** | 4.934475 | 3.443827 | **-1.490648 (-30.2%)** | **-1.490013** | output blocks median 16 -> 8, peak RSS 25,374 -> 25,148 KiB |
| **Five repeated late ZIP objects** | **4,727** | **2,203** | **-2,524 B (-53.4%)** | 10.208145 | 8.788881 | **-1.419264 (-13.9%)** | **-1.419384** | output blocks 16 -> 8; **verify/read slower by +0.177873 ms**, 0.490890 -> 0.668763 ms |
| 150 ordinary non-ZIP source files | 22,840 | 22,840 | **0 B**, identical SHA | 10.374280 | 10.366500 | -0.007781 | -0.014227 | peak RSS 24,768 -> 24,790 KiB (+22 KiB) |

## Decision
**SCOPED HEADROOM SURVIVES WHOLE-PRODUCT ACCOUNTING.** At least on a structurally late unsupported ZIP, O63 removes *physical* abandoned candidate bytes from an actual complete CMPCT archive and also reduces its measured creation wall/CPU. This is stronger than a candidate-only microbenchmark and confirms the mechanism's plausible product value. Original late-Huffman fallback becomes less wasteful without losing exact reconstruction or strong verification. In the included ordinary and early-fallback controls, archive bytes remained identical, not larger. The current corpus includes repeated ZIPs whose content deduplicates; do not extrapolate saved bytes linearly by number of ZIP objects.

**Strongest negative/self-critique:** Multiple-late read/verify became **+0.177873 ms slower** in measured medians, even though create and bytes improved. Early ZIP saw +0.0118ms create overhead. The sample is one Ubuntu host/five synthetic shapes with four ABBA blocks each, unknown cache warmth, no filesystem tree mutation during read, no Windows/macOS economics, no full serious workload matrix, and no official release-gate benchmark. Peak RSS is a process-level maximum and small interprocess differences are not allocator proof. The “regular ZIP positive control” source uses valid stdlib ZIP, but this economics instrument does not independently certify virtual-recipe admission in that control; O63's separate specialized court covers that property.

**Alternative explanation:** Some wall improvements could include instance/runner variance. Same-host ABBA with source and installed binary identity reduces, but does not eliminate, noise; deterministic byte differences and strong reconstruction are more decisive. No relaxed benchmark, comparator, relative/absolute cutoff or corpus is involved.

## Coordination / counterfactual / next gate
Prior isolated journal-cost study reported +1.553ms at 4096 candidate callbacks, not end-to-end product economics; a more causally sharp real-Builder micro A/B produced stronger evidence with only one hosted compute lane. The cleanest prospective discriminator for any proposed speculative-candidate optimization is **late fallback vs early fallback on the same unchanged source and actual Builder**, not merely instrumenting callback overhead.

The quality-ratchet observation is confined to genuine product source comparison at O63, and is not a release/promotable success. Release must still solve four inherited v0.30 fingerprint/surface generic CI failures, source-combination safety, and execute actual official same-tree r24/ZIP effective performance job. Owners of O63 and general release controls retain authority. No new Discovery Engine policy earned; `docs/discovery/STATE.json` unchanged.

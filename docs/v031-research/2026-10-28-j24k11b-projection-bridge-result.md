# J24K11b — Freshly charged VZIP row projection: hosted scientific result

Date: 2026-10-28 UTC
Status: **PROJECTION_BRIDGE_HEADROOM — FROZEN 1.5x GATE PASSED; REAL READER AND RELEASE NOT TESTED**.
Continuation of [J24K11 Draft PR #660](https://github.com/FCMO-AI/.CMPCT/pull/660).
Preregistration **before source**: `598557b1098b81219d129dab0e0271f5ac04aacc`.
**Exact measured source HEAD** `759ff40eb2a552311bfa576f9410314aa2242a17`.
[Original GitHub Actions #40655201027](https://github.com/FCMO-AI/.CMPCT/actions/runs/40655201027) **SUCCESS** (Ubuntu 24.04, CPython 3.11).
[Raw original artifact #12801875866](https://github.com/FCMO-AI/.CMPCT/actions/runs/40655201027/artifacts/12801875866), ZIP SHA-256 `98a071ec0ae70a9744fcb5426a7fbe28d027a0222caaeb42ce370df1071093c9`.

## What changed from J24K11
The earlier native speedup of >=20.9x for 4,096 modeled BHDRs assumed the seven-field Python input tuples were already available. The **stronger new court** constructs the native tuples afresh **for every timed query** from the exact r24-shaped authenticated `blobs` descriptor and `payloads` recipe representations and charges this bridge to native; the direct Python alternative consumes those original structures without a projection. Both alternatives validate the same physical bytes, signed size claim, record boundaries, flags, codec and stream coordinate.

A randomized physical-owner order in half the cells is a held-out perturbation of access pattern. The other half preserves sequential placement. Neither uses prior-query memoization, full source copies, or a saved native projection.

## Same-source 4,096-stream component result (12 observations per arm/cell)

| Modeled representation | Owner order | Strong direct Python wall | Fresh-projection+native wall | Wall ratio | New Python heap for projected tuples |
|---|---|---:|---:|---:|---:|
| STORED physical RAW | Sequential | 3.913 ms | 0.931 ms | **4.20x** | 426,264 B |
| STORED physical RAW | Permuted | 3.908 ms | 0.996 ms | **3.92x** | 426,264 B |
| Canonical Deflate mode0 | Sequential | 3.995 ms | 0.951 ms | **4.20x** | 426,264 B |
| Canonical Deflate mode0 | Permuted | 4.086 ms | 1.021 ms | **4.00x** | 426,264 B |
| Retained mode1 (opaque owner) | Sequential | 3.914 ms | 0.953 ms | **4.11x** | 426,264 B |
| Retained mode1 (opaque owner) | Permuted | 3.960 ms | 1.022 ms | **3.88x** | 426,264 B |

Frozen success criterion required **>=1.5x both wall and CPU** versus the direct Python loop on **all six** decisive cells; worst combined measured ratio was **3.874820278x**, so the scientific headroom survives this first bridge charge.

This result **materially narrows** the earlier 20–21x headline: row construction and descriptor traversal consume the majority of the previously apparent advantage. The ratio is about 4x once this modeled bridge is included. We preserve both results and neither is promoted into a public Reader performance claim.

## Independent evidence and hostile inputs
The second hosted court completed **18 cells** (64/512/4096 streams, 3 modes, sequential/permuted physical-owner layout) with three alternatives, 12 raw observations each: **648 raw CPU/wall samples**. It also checked **54 hostile source or signed-index cases** (positive and negative signed length disagreement, physical flags) against each of three strategies, with all invalid cases rejected. Its **second-root Python-stdlib referee PASS** recalculated all cell medians, source hashes, minimum ratios, and decisions, and rejected **8/8 forged receipts**.

The original J24K11 no-bridge court was repeated in the same new hosted run and passed as well: 324 additional samples, 120 semantic cases (114 malformed rejected plus six valid empty-list controls), independent 8/8 forged receipt rejection; **18.57x minimum** original direct-loop speedup on this particular rerun. Same-code original run #40654643276 had **20.90x minimum**. The experiments are not an additive 18x * 4x gain; the difference reveals charged projection overhead.

The native scanner source SHA was `05a2187c9e2e359e4004c996b6d81bbdfd34ac875bb59fb033b6c93df96a5b81`, identical to J24K11. The projection instrument source SHA was `775a47f70cfe1711c39ae8fc41a63f1fcfc2d32f8a638d0bccbbbd690d667a1a`.

## Central remaining limitations and negative economic evidence
This is still a **component oracle**, not `CMPCT.read_range()` on an installed revision-24 signed archive. Simulated BHDR payload content does not establish real Deflate/zlib/Zstd consistency, full archive crypto/index authentication, streaming extraction, source-fd immutable ownership, or partial-range SHA authentication.

A projected 4,096-header call creates **426,264 bytes of transient Python heap objects** by shallow `sys.getsizeof` accounting, besides the original blob/recipe lists. That is real allocation/garbage-collection and memory-traffic debt; no reliable peak process RSS, free-threaded Python behavior, or multicore contention result was obtained. Python allocator reuse makes simple HWM unsuitable as the only accounting method. Changing Python 3.11 to other versions, portable binary-wheel proof, concurrent same-inode archive mutation and end-to-end Reader opening/closing remain untested.

The existing J24K09 fix #653 is the product owner. The native oracle does not automatically preserve the original error *type/message*: a C `False` would need the exact Python fallback for failure. Inherited stronger signed-index, BHDR, mode2 recompression, source and recovery guards cannot be replaced by a shallow fast Boolean without hostile input testing. No live product source or format change occurred.

## Decisive continuation
The next experiment must use an **installed, source-exact J24K09 Reader on authentic signed r24**, with direct existing Python BHDR witness vs batch native plus fresh projection and strict fallback under mixed VZIP geometries, varying query locality (Q=1 and 64), actual per-read content and full zip verify, cold-open CPU/wall, peak RSS and hostile same-inode mutation. Compare a non-native vectorized Python simplification or more efficient witness representation if it reduces total product cost, and preserve a Python-only fallback.

A more ambitious direct native scanner of signed `blobs` and `payloads` could avoid constructing the 426KB tuple projection, **but requires a new preregistered security/ABI decision** and cannot inherit J24K11b's proof or assume it is cheaper. It would also raise maintenance complexity. Evaluate opportunity cost against measured #569 admission debt and the #659 published-floor residual before committing product code.

Conclusion: **two successive preregistered science questions changed decisions**: (1) native batching has real micro headroom, (2) most of its apparent gain disappears when fresh Python projection is charged, yet a 3.87–4.20x component advantage remains in the modeled large-suffix geometry. No product gain or release credit earned; published main remains v0.30.0/r24; `docs/discovery/STATE.json` unchanged, no discovery-policy change justified.

# O74 — Two S_PACK owners versus O73 split VZIP: hosted result

2026-10-25 UTC. Research evidence only; no product, release or format credit. Preregistered before implementation at commit 7b1c5e93c9aed2c48983e63950c96980a2f91530. O73's original results remain separately preserved.

## Evidence
Hosted GitHub Actions run https://github.com/FCMO-AI/.CMPCT/actions/runs/40182912249 at exact result source f5f0852ed9c2e03d3a2e4c3f279544f46091bbe7: SUCCESS; both scientific tests PASS. Artifact https://github.com/FCMO-AI/.CMPCT/actions/runs/40182912249/artifacts/12593894948 SHA-256 7be80cf7a90cbdcf76df52aafdeab43fa63a5f995bf4a69d857d33d65fbf8708. Original O74 JSON SHA-256 2c622a311ebab19f7d935cbe75bffbc9f69fe15110b3b9c6e4c3999fcddf49ec. Independent receipt audit recomputes deterministic SHA consistency, physical inputs, medians, holdout verdicts and JUnit: **131/131 PASS**. Receipts do not permit independent reexecution of original archive engine.

The same source root is built six times per four structural corpora using untouched one S_PACK, O73 large S_PACK + small VZIP, and O74 two physical S_PACK owners. Real installed CMPCT Builder Git blob 663ef0922992b1fbb8f19e6eea88d55c10a56044; no code changed on disk. Strong archive verification, all-member read and at least one full extraction per arm per corpus passed.

## Prospective primary verdict: TWO_PACK_STRONG_CONTROL

| 6 large / 2 small | Shipping one pack | O73 pack + VZIP | O74 two packs |
|---|---:|---:|---:|
| Complete CMPCT bytes | 790,524 | 791,193 | **790,674** |
| Create wall median | 8.681 ms | 8.741 ms | **7.809 ms** |
| Create CPU median | 8.682 ms | 8.743 ms | **7.810 ms** |
| 64-byte tiny selected read wall | 429.066 us | 36.368 us | **22.648 us** |
| Actual decoded blob bytes | 789,722 | **1,148** | 2,306 |
| Selected physically stored blob bytes | 789,488 | 1,116 | 2,168 |

The preregistered conjunction was satisfied: two pack saves 519 complete bytes, 0.932 ms creation, 13.721 us small read relative to O73 VZIP, with 2.009x the decoded work, below the <=3x budget. Relative to unchanged shipping, two pack reduces selected decoded work by ~342.5x, with +150 complete bytes (+0.0190%); its apparent 0.872 ms create advantage is one-run evidence, not global certainty. **No 0-byte release-parity win**. Product credit remains zero.

## Negative, hostile and counterfactual evidence

5-large/3-small holdout: shipping 660,329 vs dual 660,475 bytes. Dual pack improved total bytes/create/read over VZIP, but decoded work **3,459 / 1,148 = 3.013x**, *strictly failing* the unchanged <=3x limit. Do not round, move the limit or call this holdout a full win.

7-large/1-small holdout: shipping 920,723 vs two-pack 920,859 bytes, two-pack control passes with 1,153/1,148 decoded bytes.

8 homogeneous large, no gap: full archive size 1,050,880 B and complete archive SHA remain exactly identical for original and two-pack control; no physical split should occur.

## Decision and debt

The simpler two-pack ownership representation **subsumes O73 tiny-VZIP split on the primary tested corpus**, but is not a universal winner. The 5/3 strict control failure narrows generality and must survive future research. The O74 physical size-gap rule is research-only: not a shippable policy, not corpus-universal or proven safe under hostile source concurrency. Complete size debt +150 B vs shipping remains.

Missing: cold OS page cache/disk IO, fresh process startup, peak RSS/temporary allocation, sustained read/extract, high cross-group redundancy, multiple OS, external ZIP/Zstd, comprehensive release gate, source mutation and general admission economics. Cheapest next disproof: a preregistered high cross-group redundancy corpus where split ownership destroys meaningful compression savings, compare two-pack vs one-pack and VZIP. No version, shipped Builder, release-gate, frozen benchmark, Discovery Engine state, merge or release modifications.

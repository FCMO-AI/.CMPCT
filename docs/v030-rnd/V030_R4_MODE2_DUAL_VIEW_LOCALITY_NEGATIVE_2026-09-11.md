# v0.30 R4 Analytics Mode2 dual-view locality — negative result — 2026-09-11

Status: **FALSIFIED FOR DENSITY; LOCALITY MECHANISM WORKS; DO NOT PROMOTE**

Exact evidence authority:
- branch: `agent/v030-authoritative-integration`
- source commit: `5cbbc1d37e1c538537b7ee32421e23e6e9cff74a`
- workflow run: `34667624820`
- job: `103482677018`
- artifact: `10288634405` (`v030-r4-mode2-dual-view-locality-v2-5cbbc1d37e1c538537b7ee32421e23e6e9cff74a`)
- artifact ZIP SHA-256: `d239d3c3d365bfbd207c08b5f7a0f8506e56b6c7d587ee57c08730b371f2e47c`
- benchmark: `benchmarks/v030_r4_mode2_dual_view_locality_v2.py`
- schema: `cmpct-v030-r4-mode2-dual-view-locality-v2`

This is negative research evidence. It changes no shipping format, selector, release version, or frozen comparator result.

## Mission lock

The composed R4 gate established that Analytics Mode2 is a major density/creation-compute win but has unacceptable selective reconstruction (~937.53x worst previously observed). Conventional restart-window checkpoints had already budgeted above the available density margin.

The cheapest remaining representation-boundary hypothesis was therefore tested before inventing a new codec:

> Keep the ordinary localized external NPY representation, retain one exact NPZ physical view, segment that NPZ view into fixed 8 KiB authenticated leaves, and serve a cold 4 KiB NPZ range from only the touched segment(s), compact root/header, manifest/meta and Merkle siblings.

Pre-registered disproof law:
1. byte-exact semantic tree reconstruction must hold;
2. corruption in a touched NPZ segment must be rejected;
3. maximum cold authenticated NPZ range amplification must be <=8x;
4. **all added physical bytes must be charged and the Analytics bundle must remain below the accepted frozen/source-sealed v0.29 Analytics floor of 6,135,172 B.**

Failing either density or locality falsifies the repair.

## Hostile-review correction before adjudication

The first implementation (`v030_r4_mode2_dual_view_locality.py`) was **not accepted as locality evidence**. Hostile review found that its selective helper physically rehashed `base.cmpct`, `npy.cmpct`, and `owner.tcol` while omitting those unrelated reads from `physical_bytes_touched`.

V2 corrected only that accounting/dependency-cone defect; it did not change representation, segment size, threshold, stored bytes, or the decision law. A selective NPZ read in V2 charges the small research root/header, manifest, NPZ metadata, touched NPZ data segments, and Merkle sibling nodes. It reads zero unrelated base/NPY/tabular bytes. Full extraction continues to validate the complete bundle. The compact root/header is research packaging, **not** claimed as the final product cryptographic layout.

## Exact result

| Metric | Result |
|---|---:|
| ordinary v0.30 Analytics | 10,392,498 B |
| retained Mode2 Analytics | 4,197,642 B |
| dual-view candidate | **7,782,072 B** |
| accepted v0.29 Analytics floor | **6,135,172 B** |
| extra bytes versus Mode2 | **+3,584,430 B** |
| margin versus v0.29 | **-1,646,900 B** |
| max cold authenticated 4 KiB NPZ amplification | **4.404541015625x** |
| exact semantic tree | PASS |
| touched-data corruption rejection | PASS |

Hypothesis outcome:
- exact tree reconstruction: **PASS**;
- cold authenticated NPZ range <=8x: **PASS**;
- corruption rejection: **PASS**;
- dual view stays below v0.29 Analytics: **FAIL**;
- supported for next hardening: **FALSE**.

## Interpretation

The experiment cleanly separates the two problems:

- fixed-size authenticated segmentation is sufficient to repair selective NPZ locality in principle;
- **duplicating the exact NPZ physical view is economically unacceptable**.

The candidate spends `3,584,430 B` over Mode2 to buy locality, exceeding Mode2's `1,937,530 B` approximate byte margin below v0.29 by about `1.647 MB`. This is not a near miss that warrants threshold tuning. The representation duplicates too much information.

The result therefore strengthens, rather than weakens, the owner-boundary diagnosis: locality must be bought with **restart/addressability state that is materially smaller than a second full physical view**.

## Decision

`REJECT_FULL_DUAL_VIEW; ADVANCE_MINIMAL_RESTART_STATE_OR_INDEPENDENT_CHUNK_OWNERSHIP`.

Do not:
- relax the <=8x locality requirement;
- hide the exact NPZ copy outside authenticated stored-byte accounting;
- revive generic 32 KiB restart windows that already exceeded the density budget;
- tune the 8 KiB leaf size to make this representation appear economically viable. Leaf tuning can change authentication overhead, but cannot erase the multi-megabyte cost of retaining a second NPZ view.

Next falsifiable line: preserve the single Mode2 information owner and quantify the **minimum exact decoder/reconstruction state per independently addressable region**. A viable design must keep total restart/chunk metadata plus any necessary boundary residue inside the real Analytics density margin while delivering <=8x physical/reconstruction work and exact DEFLATE/NPZ bytes. If exact mid-stream Deflate reproduction requires state too large or non-portable, change the ownership representation so the exact compressed stream itself is stored once in independently addressable chunks rather than regenerated from a monolithic transform.

## Composed-frontier context

The prior exact 15-workload composed gate remains authoritative:
- same-run v0.30: 150,059,822 B;
- composed Mode2 + Office SFV2: **138,616,788 B**;
- frozen v0.29: 137,499,525 B;
- remaining aggregate gap: **1,117,263 B (~0.813%)**;
- composed creation tree CPU improved by **321.894083 s** versus the same-run v0.30 baseline.

This negative does not retract the composed density result. It says only that a full exact NPZ dual view is not an acceptable way to rehabilitate Analytics locality.

## Frozen ONE context

The ONE Genesis verdict remains unchanged. v0.30 is the primary near-term line; ONE remains preserved secondary evidence. The useful ONE lesson here is specifically elimination of redundant physical information and cheap bounded access—not duplication of a second representation merely to obtain locality.

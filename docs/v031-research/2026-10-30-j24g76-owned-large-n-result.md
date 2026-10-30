# J24G76 — held-out large-N owned decoder Reader result

**Date:** 2026-10-30 UTC. **Scientific verdict:** `HELDOUT_LARGE_N_OWNED_H1_SURVIVES_3_OF_3`, research only. **Release/product credit: 0.** No merge, format, ABI, shipping Reader, benchmark comparator or release change.

## Source, authority and immutable prediction

- Repo: `FCMO-AI/.CMPCT`, [draft PR #823](https://github.com/FCMO-AI/.CMPCT/pull/823), child of experimental #820 **exact** `c15459f70001800f3781925efc7356409eb03ffe`. Preregistered scientific question **before any new experiment source** at `0de1e97d7a6482c1dd08c643174385e78a5602f6`. First result-bearing workflow/source HEAD `5aa79418d70a200aa64253b1de8855ac98787f8e`.
- Frozen `src/cmpct/reader.py` Git blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`, inherited #820 research `research/j24g74_owned_decoder_court.py` blob `9af74e26e7585f6d88b1d59ead86514f41b0e373` and general #808 helper blob `7657a41d11f2b3c8136c0b69cfe62401f9b19ccb`. Workflow attested ancestry and exact blobs on all three hosts.
- Prespecified H1: *each* 8,192/middle and 32,768/tail family must show **>=1.20x owned/factored warm complete Reader-open** with **nonincreased median Python traced peak** in **>=2 of 3 OS**, while every physical archive semantic/integrity/recovery gate passes. The first 2,048-member, front-delete evidence in #820 was **inherited**, not counted as held-out.

## Authentic physical experiment and measured result

[GitHub Actions #41040878199](https://github.com/FCMO-AI/.CMPCT/actions/runs/41040878199) succeeded on Ubuntu 24.04 / macOS 14 / Windows Server 2022; exact HEAD `5aa79418d70a200aa64253b1de8855ac98787f8e`. Every host created **two real Builder/public-Writer revision-24 archives**: 8,192 initial + 63 *middle* deletions (=8,129 live) and 32,768 initial + 63 *tail* deletions (=32,705 live). Each archive contains **64 signed physical footers (one checkpoint + 63 one-operation delta generations)**. Same physical bytes within each A/B/C comparison; filesystem metadata makes archives differ across OS.

All medians below are complete **warm in-process Reader constructor** wall milliseconds, 12 recorded balanced ABC/ACB/BAC/BCA/CAB/CBA order samples for *each* variant/host/family. Not fresh-process import/startup or cold disk.

| Host | Input/deletion family | Original Reader ms | Copy-preserving Factored ms | Fresh-owned ms | Marginal factored/owned | Original/owned |
|---|---|---:|---:|---:|---:|---:|
| Ubuntu | 8,192 / middle | 206.531 | 52.715 | **14.082** | **3.744x** | 14.667x |
| macOS | 8,192 / middle | 194.509 | 49.142 | **13.247** | **3.710x** | 14.683x |
| Windows | 8,192 / middle | 247.275 | 65.295 | **18.040** | **3.619x** | 13.707x |
| Ubuntu | 32,768 / tail | 1123.270 | 279.178 | **79.887** | **3.495x** | 14.061x |
| macOS | 32,768 / tail | 1202.839 | 278.481 | **84.031** | **3.314x** | 14.314x |
| Windows | 32,768 / tail | 1264.242 | 307.933 | **87.705** | **3.511x** | 14.415x |

**Observed scientific decision: H1 passed 3/3 on each large-N family, stronger than the registered 2/3 requirement.** All six sets retain positive >=3.31x median marginal speedup, with nonincreased Python allocation. The gain from the released Reader to research-owned is ~13.7–14.7x **on these exact workloads only**. No published product improvement or general workload guarantee is implied.

### Python allocation, process memory, and creation economics

Median tracked Python peak allocations, factored → owned:
- 8,192: Ubuntu **10,520,415 → 5,975,559 B**, macOS **10,528,871 → 5,984,015 B**, Windows **10,467,546 → 5,922,690 B**; **−4,544,856 B** all three.
- 32,768: Ubuntu **39,616,032 → 21,233,528 B**, macOS **39,616,206 → 21,233,646 B**, Windows **39,620,263 → 21,237,759 B**; **−18,382,504–18,382,560 B**.
- Fresh-process RSS peaks (median) are **not** equivalent to Python tracked peak. 32,768: macOS **78,659,584 → 56,049,664 B** and Windows **69,939,200 → 49,717,248 B**, but **Ubuntu 170,823,680 → 170,823,680 B** (same reported peak despite lower post-close RSS). That Ubuntu counterexample prevents claiming universal peak-RSS dominance; the Builder/verification and process high-water mark may dominate the small Reader comparison.
- 8,192/32,768 archives in bytes (Ubuntu): **931,215 / 3,738,563**; (macOS): **939,497 / 3,764,495**; (Windows): **874,115 / 3,476,739**. Reader-only A/B/C writes **zero new archive bytes**; stored bytes reflect genuine physical Writer costs, not a superior new archive representation.
- Recorded combined source-tree+Builder wall seconds, 8,192/32,768: Ubuntu **0.659 / 2.801**, macOS **1.400 / 8.316**, Windows **4.747 / 15.745**. Authentic **63 Writer deletes wall seconds**: Ubuntu **7.306 / 37.255**, macOS **6.448 / 33.526**, Windows **9.571 / 42.869**. This enormous per-operation Writer cost is **not fixed** by optimizing the Reader. It is arguably a more important *whole-system* performance debt.
- CPU wall split is retained in the original raw receipts. Windows short-case CPU clock granularity precludes nanosecond attribution, and macOS process performance is variable. Independent two-block median factored/owned ratios remain positive (Ubuntu 8,192: 3.79/3.04, 32,768: 3.45/3.48; macOS: 3.82/3.24 and 3.29/3.08; Windows: 3.72/3.16 and 3.54/3.45). Do not claim deterministic speedups across hosts.

## Physical integrity, independent checks and original artifacts

Detached no-CMPCT `research/j24g76_detached_audit.py` verified each real archive from original ZIP bytes: complete SHA-256, physical MessagePack/Zstd footer chain, **63 exact registered middle or tail deletion paths**, original and final file counts, authenticated index hash, all 36 raw per-case timing samples and medians, CPU and tracked peak receipts, and recoverable depth-62 state on corrupt/truncated last footer. The physical parser rejected an actual footer digest mutation. Six deliberately forged *receipt* mutations were independently rejected per host (**18/18**). All original Reader, copied Factored, fresh-owned Readers and structural preflight returned identical effective indices. `verify()` and `read()` checked all surviving file bytes against original SHA-256-derived payloads (not only an index digest).

| Host | Original artifact | Provider ZIP SHA-256 |
|---|---|---|
| Ubuntu | [#12970745244](https://github.com/FCMO-AI/.CMPCT/actions/runs/41040878199/artifacts/12970745244) | `ee0ace3bf61d700033a029057cd7f930e23cc30ceea9f0f60446308a0e7b4968` |
| macOS | [#12970780152](https://github.com/FCMO-AI/.CMPCT/actions/runs/41040878199/artifacts/12970780152) | `aff49eee37cbbffba5e04f223796ea5c1190039cf43f386eb72036a9f921f843` |
| Windows | [#12970157368](https://github.com/FCMO-AI/.CMPCT/actions/runs/41040878199/artifacts/12970157368) | `cf31611ba6a88718dfb7cb3cb66329a0a1641d5c3d2ade70315055c5ca49e398` |

All three provider ZIPs were **downloaded again**, and their SHA-256 digests rehashed to match the provider; extracted physical files were independently SHA-256 checked against their receipt, and raw medians/block ratios recomputed locally. This is a second analysis of original archived bytes, not only hosted stdout.

## Strongest negative, causal interpretation and unearned claims

The central positive result generalizes the **experimental** private fresh-decoder ownership transfer beyond the earlier N=2,048 case and across index positions. But transfer itself changes/mutates the decoder's local MessagePack objects; this is safe only while their graph is unescaped and privately owned. The explicit retained-caller counterexample **demonstrated mutation of externally held input**; do **not** remove deep-copy from a shared/public helper. The Reader's exposed `index/files/by` descriptors are also mutable after initialization, and public mutation semantics have not been hardened.

An important counterweight emerged from full-system accounting: a 32,768-file journal with 63 one-op deletions needs **33.5–42.9 seconds just to append those 63 operations**, while the optimized Reader opens in ~80–88 ms. Writer update economics, hardlink/xattr semantics, 64th checkpoint, hostile parser ceilings, memory ownership across native FFI, extraction and cold disk are **not** resolved by this science. The Ubuntu unchanged peak process RSS is a measured contradiction to a universal physical-memory claim, not to the narrower Python allocation H1.

Hardlinks and POSIX sparse xattrs were not included in the held-out large-N file family. Their existing positive physical evidence belongs to #817, not to this result. Do not claim correctness under unseen composition. No fresh-process CLI create/extract or same-tree ZIP/Zstd competitor benchmark. No merge or release, credit = 0.

## Decision, coordination, counterfactual and next executable action

**Scientific question changed decision**: held-out large-N evidence supports keeping *one* owned-decoder research path for source-exact integration exploration rather than retiring it as an N=2,048 artifact. H1 survived all tested hosts and both index positions; stronger generality still requires mixed true filesystem metadata and composition with hardlink guard. No concurrence collision: #820 owns the algorithm; #795 the signed Reader product seam; #815/#817 hardlink correctness; #822 CI custody; #574 shared Discovery `STATE.json`. This branch edits only separate research, standalone auditor, workflow and research notes, with no shared state mutation.

A useful counterfactual prospective discriminator is to test a scaling/position perturbation *before* spending on a product integration. This experiment delivers that evidence, but alone does not warrant a Discovery Engine policy amendment. **Next priority**: integrate under #795/#817 ownership, preserving signed-xattr lineage, hardlink owners, writer checkpoint64, recovery and public alias contracts; only then execute complete size/create/extract/RSS/cold-open/native & official release gates. Parallel engineering should separately address **writer 63-operation append cost**, now directly measured. Keep the simple #811 DELETE bisect as a lesser-complexity control if owned replay introduces broad costs.

## CI source scope

- Scientific execution **#41040878199 exact source HEAD**: three specialized jobs **SUCCESS** and original no-CMPCT artifact checks **PASS**, all six scenarios source-bound.
- Initial Engineering Evidence runs failed due PR dossier headings and missing quality-ratchet text; **corrected PR metadata without changing evaluator or source**. Later run **#41041145398 SUCCESS** at measured HEAD.
- Version Discipline, CI Topology, R36 attribution and J24G41 Darwin succeeded on the result-bearing HEAD. General Tests was in progress at initial source-audit time and must be reported from its final exact run separately.
- This documentation-only result commit changes the git commit HEAD but *not experiment source blobs*. Treat any new post-result CI as **pending** until it actually finishes. Do not promote from the prior source run.

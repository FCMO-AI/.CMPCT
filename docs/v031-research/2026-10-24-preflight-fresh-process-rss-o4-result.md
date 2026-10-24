# O4 — source-exact signed preflight: resident-memory evidence

## Provenance and observation boundary

**Decision record:** 2026-10-24 UTC. This is a *scientific* same-package/same-archive preflight comparison, not a core release, native ABI claim or full release performance gate.

- Locked preregistration **before instrument or results:** `a42cede08f1efa0fbe396cdae5aa3dcb6144749c`.
- Combined product owner: [PR #348](https://github.com/FCMO-AI/.CMPCT/pull/348) `0062961be78cd4d28231a9acaf37a4d9cf43920c`, exact `validation.py` blob `1e085db992add64118a9488790096c574fff154d`. **No product source changed**.
- Historical replay comparator: complete `_apply_delta` lifted verbatim from historical Git `validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`; the surrounding combined validator remains identical across both engines.
- Exact evidence-running HEAD: `e46207d9902c3748977ec35588995a51f10f06d9`.
- [Source-bound GitHub Actions run #40092228664](https://github.com/FCMO-AI/.CMPCT/actions/runs/40092228664) **SUCCESS**, Linux Python 3.11, five independently spawned child processes per arm/size/case and deterministic A/B/B/A rotation.
- [Raw receipt artifact #12559531162](https://github.com/FCMO-AI/.CMPCT/actions/runs/40092228664/artifacts/12559531162), zip SHA-256 `9db87c4c1d55ac7b8c3b148399a69c0915e95aabd05fe3a6dadf74a27104de3d`, inner JSON `fresh-process-rss-o4.json` SHA-256 `8faa61e5a5a94f1e0c0f048f5a11e825a6ecab177966fd005c1bb0d11b75745e`.

Both arms processed the **same signed revision-24 archive for each case**. The fully authenticated delta and final-state-equivalent checkpoint had identical physical bytes and matching logical member/content semantics, while differing in authenticated journal history. All source, hash, file-count and delta-depth guards passed.

## Measured medians (five fresh processes per arm)

| Signed file count | Case | Historic preflight wall | Combined preflight wall | Historic / combined maximum child RSS | Historical / combined live-RSS increase during measured call |
|---:|---|---:|---:|---:|---:|
| 512 | delta | 9.699 ms | 2.923 ms | 27,688 / 27,688 KiB | +916 / +932 KiB |
| 512 | checkpoint | 2.132 ms | 2.137 ms | 27,688 / 27,688 KiB | +832 / +856 KiB |
| 2,048 | delta | 124.018 ms | 10.836 ms | 30,564 / 30,564 KiB | +2,176 / +2,416 KiB |
| 2,048 | checkpoint | 7.486 ms | 7.577 ms | 30,564 / 30,564 KiB | +1,756 / +1,872 KiB |
| **4,096** | **delta** | **486.198 ms** | **21.240 ms** | **33,776 / 33,776 KiB** | **+2,528 / +3,804 KiB** |
| 4,096 | checkpoint | 15.110 ms | 15.162 ms | 33,776 / 33,776 KiB | +2,996 / +3,132 KiB |

For 4,096 signed renames, the combined validator is **22.89× faster** in this fresh-process court. This is independently consistent in direction with [PR #347](https://github.com/FCMO-AI/.CMPCT/pull/347)'s stronger source-exact same-runner 25.18× ABBA result; it is not an additional universal performance claim. The 4,096-operation archives used **12,046 total stored bytes** versus **4,601 bytes** for the logically equivalent checkpoint.

## Strongest negative, uncertainty and decision

**High-water RSS alone was *not a sensitive discriminator here*.** In every child `ru_maxrss` was **already at its final value before timed preflight**, so its zero before/after difference is not evidence of zero transient memory cost. Process high-water can have been set by imports/allocator initialization. The post-call Linux `VmRSS` readings show a bounded **+1,276 KiB extra** median live-RSS *increase* for the indexed delta arm at N=4096 versus historical (3,804 vs 2,528 KiB), with +136 KiB extra for the equivalent checkpoint. The checkpoint-adjusted difference-of-differences is approximately **+1,140 KiB**. This is consistent with the inherited Python `tracemalloc` allocation debt (+42.77% at N=4096) and contradicts any blanket claim that indexing is memory-free.

**Decision:** At N <= 4,096, the directly observed live-resident delta is below the preregistered materiality discriminator (8 MiB absolute or 10% of overall resident process) and the CPU win is substantial. **Do not immediately redesign or reject the indexed replay due solely to the traced allocation increase.** Preserve a **nonzero, size-dependent RSS and maximum-RSS measurement ambiguity**, not a Pareto dominance claim. The question at larger legitimate file counts remains open. No complexity reduction has been demonstrated, no official performance gate has been passed, and the reported high-water statistic cannot resolve intermediate replay peaks.

## Counterfactual and future work

A low-cost child-process trial with **before/after live VmRSS** added alongside `ru_maxrss` would have exposed the 1.1 MiB checkpoint-adjusted resident cost earlier and avoided interpreting a saturated high-water mark as a zero-cost result. No discovery-policy rewrite is justified by one trial. If further product work is warranted, run an **explicitly preregistered higher-N continuation** and an independent intra-call peak sampling approach before changing the proven algorithm. Product work still needs complete shared-HEAD integration, exact-head general CI, cross-platform recovery, RSS, and official non-skipped release parity.

The original owners' source and evidence remain untouched. This document records both positive and negative result without promoting the draft.

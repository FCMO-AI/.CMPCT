# J24G60 — three-host result: ordinary public Writer depth-63 cold-open cost

Date: 2026-10-30 UTC  
Status: **DECISIVE SOURCE-EXACT RESEARCH-ONLY MECHANISM EVIDENCE; NOT A RELEASE/PRODUCT WIN**.  
Preregistered first at `ad718f59f346e6ce21ec1b45d2e5747748389052`. Measured source HEAD `589141cd896729d6ee7616344900ea5256e05aac` (tree based on exact #795 `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`).

## Result-bearing GitHub evidence
[GitHub Actions #40995641799](https://github.com/FCMO-AI/.CMPCT/actions/runs/40995641799): **SUCCESS in all three** independent hosted jobs:
- Ubuntu 24.04 original ZIP [artifact #12951231930](https://github.com/FCMO-AI/.CMPCT/actions/runs/40995641799/artifacts/12951231930), ZIP SHA-256 `16ab0e75aa7510474bee535c3a49256ed7a67cd9bd84e7eb6d6c97f916336780`, raw JSON SHA-256 `0744e934a1fb2d1f0f1a6e482b98add39b45629e99505d04566622839c395ad6`.
- macOS 14 original ZIP [artifact #12950983366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40995641799/artifacts/12950983366), ZIP SHA-256 `be56e3a59037e79d5b92a695165dc1b315ac5bd5ee8aaaae08a9fcb689b8d6bc`, raw JSON SHA-256 `6c77652aa1c5fb950ea78537ea9d626f17cc5ec27e5e4c7a4d9db63cddccd8e6`.
- Windows 2022 original ZIP [artifact #12950784511](https://github.com/FCMO-AI/.CMPCT/actions/runs/40995641799/artifacts/12950784511), ZIP SHA-256 `2784e83fca96c9111a7a19abbfde3d9df626f53601f1686d84feccf06a389540`, raw JSON SHA-256 `202f641cb692b03b76fe383b22abd26ef62d385e916ab60db6f1cfcad080d6a3`.

Source blobs authenticated in workflow and test: Builder `a2160a2`, Reader `29a8be6`, Writer `3eef7fd`, journal replay `03743ca`, validator `5ea3b8f`. No product engine, source grammar, release comparator, benchmark or on-disk format changed.

## Primary matched real-archive result: 2,048 members, 63 public one-op deltas

| Host | Chain open median | Extra same-state checkpoint open median | Difference | Ratio |
|---|---:|---:|---:|---:|
| Ubuntu | 27.621 ms | 2.764 ms | 24.857 ms | **9.994×** |
| macOS | 36.775 ms | 3.142 ms | 33.632 ms | **11.702×** |
| Windows | 58.352 ms | 4.049 ms | 54.303 ms | **14.412×** |

All three hosts crossed preregistered **research selection** criterion 10% + 3ms. This is a *Reader open-only* metric, excluding import/process startup, extraction, create, full verification, disk-cold cache, peak product RSS and end-to-end ZIP/Zstd parity.

Archive sizes on primary trial: authentic chain **292,396 B**, extra checkpoint representation **305,055 B**, i.e. **+12,659 B / +4.3294%** additional stored bytes. Full checkpoint was appended to a *separate copy* of the genuine chain and retained the prior chain; it is a deliberately charged **same-logical-state oracle**, not a currently shipped public 63rd-op Writer behavior. A legitimate product solution must prove this storage, write, durability, recovery and metadata tradeoff against direct public Writer semantics and strict zero-byte promotion floor. The normal 64th Writer operation already checkpoints, so 63-depth is the worst regular case.

## Structural transfer / scaling controls

Ubuntu 512 entries, depths 1 / 16 / 32 / 63, chain vs checkpoint medians:
`0.791/0.647`, `2.382/0.648`, `3.985/0.653`, `6.882/0.656` ms.

Ubuntu 2,048 entries, depths 1 / 16 / 32 / 63:
`3.285/2.733`, `9.250/2.743`, `15.617/2.798`, `27.621/2.764` ms.

Windows at 2,048 entries (depths 1/16/32/63):
`5.354/3.969`, `18.451/4.087`, `32.183/4.081`, `58.352/4.049` ms.

Growing per-generation chain cost while checkpoint-open remains almost fixed supports *repeated cross-generation index replay*, not the large single-generation #797 helper scenario. macOS shows the same direction. **No direct profiling isolates the exact subroutine**—index decoding/decompression, footer scanning and rekey may contribute; do not assert all penalty is caused by name scanning.

## Exactness and evidence integrity

Every host used real Builder-generated r24 files, all 63 authentic public `append_rename` calls, 4 distinct depths, SHA-verified committed wire footer chains (all one-op deltas), a private same-state checkpoint, and identical Reader effective-index, content SHA/verify and bounded preflight files. Each host preserved **128 raw ABBA/BAAB fresh-process observations** (8 repetitions per variant per case).

A detached standard-library-only offline audit of the *original provider ZIPs* verified all 3 ZIP digests, the recorded source SHA, 384 raw samples, alternating sequence/block identity, reported medians/CPU/ratios, signed-footer records and successor links, equal-index/preflight receipt fields, checkpoint-byte premiums and 8/8 falsifying receipt mutations. This is **receipt validation**, not a second independent physical Reader re-execution. On Linux at N=2048,d=63, median VmHWM after open was 30,040 KiB chain vs 29,970 KiB checkpoint; import/allocator baseline dominates, so **no significant memory gain is claimed**. VmHWM unavailable on macOS/Windows in this harness.

## Critique, decision and next owner action

The earlier J24G58 33.266× single-generation indexed-helper result is genuine but J24G59 independently proved it *unreachable* for ordinary Writer (one op/delta). J24G60 reveals a **different, actually Writer-reachable and cross-platform measurable** cost owner: chain depth × effective-index re-materialization. This narrows productization priority to bounded cross-*generation* reuse, grouping/checkpoint ownership or a provably smaller independent representation, **not** gratuitous wide-generation indexing.

Cheapest next substantive experiment for #795/#789 owners: on physical depth-63 public archives with mixed rename/put/delete, xattr/owner lineage and recovery perturbations, compare (A) unchanged one-op per-generation reference, (B) exact semantics-preserving single-pass shared replay **without extra stored bytes**, (C) explicitly charged checkpoint alternative; measure full Reader cold/open CPU/wall, resident RSS, temp I/O, archive bytes, strong verify, recovery and Windows/macOS/Linux parity. Only if this survives should a product patch be promoted. Safety publication #749 and other current merge blockers remain independent.

No changes to `docs/discovery/STATE.json` (#574 owner), frozen comparators or release law. No merge/release. The Discovery Engine changed a **research priority**, not a policy; no general L2 policy lesson is yet earned. The transferrable counterfactual: ***first authenticate the public Writer's operation width and chain geometry; then time ordinary Reader cold-open before investing in a single-batch indexed fast path***.


## Stronger inherited alternative — discovered during counterfactual replay (2026-10-30 UTC)

Before proposing another cross-generation index, the repository's **existing historical O7/O9 family is a stronger and simpler candidate for reuse**:

- [O7 PR #358](https://github.com/FCMO-AI/.CMPCT/pull/358), exact hosted [Actions #40101351497](https://github.com/FCMO-AI/.CMPCT/actions/runs/40101351497), already reused the strict indexed validator replay in ordinary Reader. It measured actual 512-/2048-/4096-op Reader-constructor medians **3.877→1.239 ms (3.13×)** / **53.346→5.006 ms (10.66×)** / **240.870→10.140 ms (23.76×)** on its own source against a frozen original. It also recorded a checkpoint open near parity (4.022 vs 4.212 ms at 4096). Those measurements are **not J24G60 #795-source evidence** and cannot be transferred as product credit.
- [O9 PR #364](https://github.com/FCMO-AI/.CMPCT/pull/364) composed prior indexed replay and prewrite safety, with independent [O11 #368](https://github.com/FCMO-AI/.CMPCT/pull/368) installed Reader cold/RSS economics; [O10R #365](https://github.com/FCMO-AI/.CMPCT/pull/365) then added signed-generation resource ceilings. Do not transplant any pre-security version or skip inherited policy limits.
- Current #795 shared `journal_replay.py` protects **fsmeta path lineage, complete opcode admission, footer fail-close and Reader/preflight/Writer checkpoint parity**, which prior O7 may not cover. Therefore the highest-value next design is a **source-exact semantic transfer test** from O7's indexed cross-generation ownership into the newer #795 unified replay, retaining every new safety/lineage and hostile bound. First compare source-level acceptance grammar and run a charged micro against current #795 on the same physical single-op histories; no naive whole-file replacement, no duplicate authority.

**Counterfactual:** source search of O7/O9 before our J24G60 run could already have nominated cross-generation indexing as a *known prior mechanism*; however J24G60 adds decision-changing **current #795 source + 3-host measured 63-operation product applicability**, establishing that the older result warrants careful modern transfer rather than fresh invention. This is a narrow prospective lesson for the branch, **not** justification for Discovery Engine policy self-modification. Preserve all original measurements and negatives.


## Source-exact correction to prior-art interpretation (same activation, before promotion)

The initial historical O7/O9 paragraph above is **overbroad if read as a solved single-op cross-generation optimization**. Direct inspection of O7 [PR #358 source `validation.py@2bb3f53c918ae93efb105364e2b93ea46aeca034`](https://github.com/FCMO-AI/.CMPCT/blob/2c5334392c57f9c0f685c3751712acf0e242efae/src/cmpct/validation.py) proves its `_apply_delta_indexed` fast path is entered only when **`len(ops)>=8 and len(files)>=64`**. Its Reader applies the helper **one delta at a time** (see source `reader.py@6de2edcf5b804e224a1c651ca77361af5667dc2e`). Thus O7's impressive 3.13×/10.66×/23.76× results are for its own genuine multi-operation-per-generation setup, **not evidence that it speeds ordinary Writer's 63 successive *single-op* generations**.

What *can* transfer from O7: bounded indexed position/duplicate semantics, independent source/evaluator discipline and possible data-structure architecture, **after** changing ownership across generations while preserving #795's path-based fsmeta metadata lineage and fail-closed grammar. What *cannot* transfer: the measured multiplier, the current `len(ops)>=8` trigger, a whole-file transplant or blanket claim the current ordinary public Writer debt is already solved.

The decision from J24G60 remains **unchanged**: 3/3 actual public Writer single-op chain cold-open excess is physically real on the measured current #795 source. The strengthened next discriminator is a carefully bounded, *truly cross-generation* replayer (or checkpoint ownership experiment), with the historical O7 **multi-op** behavior used only as an engineering prior, and original per-generation `_apply_journal_ops` as strict control. This source-bound correction is appended rather than deleting the original counterfactual, preserving the chain of scientific reasoning. No Discovery-wide policy conclusion is earned.


## Raw-sample sensitivity and simple causal cost envelope

The detached independent receipt auditor additionally checked **all 384 process samples** rather than accepting reported aggregates. At **N=2048,d=63**, the eight **individual** wall samples per variant had **no overlap** on any host (millisecond intervals):

| Host | chain minimum–maximum | extra-checkpoint minimum–maximum | four paired ABBA block differences |
|---|---:|---:|---:|
| Ubuntu | 27.087–28.422 | 2.627–2.832 | +24.781, +24.549, +24.964, +25.573 ms |
| macOS | 34.766–39.530 | 2.300–3.468 | +33.189, +35.253, +33.119, +33.812 ms |
| Windows | 57.075–60.451 | 3.886–4.896 | +53.923, +53.364, +55.041, +55.537 ms |

Unadjusted four-depth linear fits of observed **chain** time vs depth yield per-generation slopes, for 512 and 2,048 entries respectively, of **0.0979/0.3924 ms (Ubuntu)**, **0.1595/0.5199 ms (macOS)**, and **0.2160/0.8539 ms (Windows)**. This is consistent with repeated N-dependent replay as depth increases; a four-point slope cannot prove the precise complexity class or allocate cost among sorting, metadata lineage, footer decode and validation. The check reinforces the **real measured opportunity** while not relaxing any product-economics, storage or security requirements.

# Native PACK owner admission — O8/O8b decision-complete result

Date: 2026-10-24 UTC. **Scientific status: ADMISSION CAUSALITY CONFIRMED; GENERAL-PURPOSE PROMOTION UNPROVEN.** This is not a release or on-disk-format change.

## Exact-source custody and two immutable prospective questions

- PR #330 is a disjoint scientific extension of PR #327: inherited product/C consumer SHA **`030bd50aff682592f67eba1dc5376b83bfe83fae`**; no native, C ABI, Builder/Reader, codec, format, release gate or v0.30 historical benchmark modification.
- O8 question frozen in `NATIVE_PACK_HELDOUT_O8_PREREG.md` at commit `5d2998d26348c4e202e9e97db1bcdbba82e37f6c` before experiment implementation; hosted run [40066222077](https://github.com/FCMO-AI/.CMPCT/actions/runs/40066222077), exact experiment commit `a1af021d6b91c450079356b2b35862defc2d7f4d`, artifact **12549077739**, ZIP SHA-256 `9bbe4ce5905e2d61783d3974dc0da8b2bfcdd7e0ddb87fffd6d6750499f33521`, `result.json` SHA-256 `341d0d6c8cb017785b99d2281c923b2df12bad3e673ca57cc46251849b432b55`. **96/96** independently SHA-exact C process extractions, 4 ABBA blocks × 6 sources. No file/path mismatches.
- O8 gave **zero admitted PACK batches on all 6 `.dat` cohorts**. The grouped C mode performed 100% per-entry fallback; observed grouped/serial wall ratios 0.9908–1.0051. This is valid negligible-admission-cost evidence, **not** native batching generality/performance evidence. Parent O7 ~9.52× remains a separate favorable-case result.
- Causal diagnosis: actual `src/cmpct/builder.py::_build_micro_packs()` requires `any(x in TEXT_EXT for x in c.hints)`; `src/cmpct/codec.py` lists `.txt` but not `.dat` among text hints. This original O8 test-generation error was discovered **after** the frozen O8 run. Its prereg, file and observations were not modified.
- O8b **new question frozen before new code** at `NATIVE_PACK_HELDOUT_O8B_PREREG.md` commit `878a92e5f1a1909610c68759cb7215d8bb1038b7`. Eight `.dat`/`.txt` source-content-identical controls (4 families), 4 ABBA blocks/cell, 128 independent fresh C-process exact extractions. Hosted [run 40066551832](https://github.com/FCMO-AI/.CMPCT/actions/runs/40066551832) **SUCCESS**, exact head `c26bbd62c14478e9324e84495df40f5ffb42c57e`, artifact **12549244335**, ZIP SHA-256 `b3fc77a26d663b233271ba89d29cc7a26e918cd71caa02cf9cbf03e0a2584c47`, `result.json` SHA-256 `f8a7acc96aa595613d81a80a83eb1756e27e2adbdf3805f7617e796189006a52`. **128/128** complete byte-exact archive reconstruction checks, no dropped ABBA observations, source archive hash remained unchanged on every trial.

## O8b directly measured (on the same runner within each cell)

| Content family | Suffix | Stored .cmpct bytes | Batches / batched / fallback | Serial wall median | Grouped wall median | Within-cell serial/group |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Related 256 | `.dat` | 47,224 | 0 / 0 / 256 | 11.026 ms | 11.061 ms | 0.997× |
| Related 256 | `.txt` | 4,505 | 1 / 256 / 0 | 88.630 ms | 9.748 ms | **9.093×** |
| Independent 256 | `.dat` | 217,030 | 0 / 0 / 256 | 9.698 ms | 9.709 ms | 0.999× |
| Independent 256 | `.txt` | 199,562 | 0 / 0 / 256 | 9.638 ms | 9.656 ms | 0.998× |
| Duplicates 256 | `.dat` | 1,422 | 0 / 0 / 256 | 10.681 ms | 10.723 ms | 0.996× |
| Duplicates 256 | `.txt` | 1,491 | 1 / 256 / 0 | 10.697 ms | 9.183 ms | **1.165×** |
| Mixed 257 | `.dat` | 202,837 | 0 / 0 / 257 | 10.808 ms | 10.817 ms | 0.999× |
| Mixed 257 | `.txt` | 172,651 | 1 / 256 / 1 | 97.541 ms | 10.344 ms | **9.430×** |

Across the extension twins, source payloads and per-file sizes are exactly identical; only names `.dat` vs `.txt` differ (the 70 KB `.bin` fallback is identical). Complete source byte multiset SHA-256 is equal within all pairs. **Filename semantics differ; these cross-extension byte differences are NOT valid same-path release parity comparisons.**

### Decision-changing results

1. **Admitted shared PACK related content:** 256 files, one verified batch; ~9.09× full C consumer wall improvement (and ~9.19× CPU using 88.461 ms vs 9.624 ms), with exact output. Mixed structural+noise: 256 grouped/one fallback, ~9.43× wall and ~9.56× CPU.
2. **Independent entropy:** `.txt` admits zero PACKs even with the extension hint; file bytes ↓8.05% versus `.dat` but *not* due to PACK grouping. Other encoder policy/codec/hints affect stored bytes. No grouping speedup. This **falsifies** any simplistic claim that extension alone guarantees a PACK.
3. **Exact duplicates:** `.txt` does admit 256 aliases to one PACK. Wall improves only ~1.16× and complete archive is **69 bytes larger** (4.85%) than `.dat` archive; this is an admission-cost warning, **not** proof that packing regresses same-path storage because extensions change the archive and codec policy.
4. **Fallback cost:** `.dat` arms give 100% unsupported/fallback and near-equal wall/CPU at all tested cardinalities; generic native owner-discovery traversal need not be expensive for these six small test cohorts. No broader allocation or SSD I/O claim.
5. **Whole-process RSS:** for every individual cell, serial and group process `ru_maxrss` medians match, but different extension cells have different RSS. This cannot establish zero incremental allocations, nor an arbitrary-extraction memory bound.

### Anti-bias / counterfactual / opportunity next

The first O8 result was scientifically uninformative for batching because the experiment never asserted the mechanism was admitted. The cheapest **prospective** discriminator would have been a `TEXT_EXT` lookup plus an actual `batched_members>0` condition in an admission-positive control. Preserve O8 as a useful negative/no-admission benchmark, not a failed generalization claim. This supports experiment-design improvement but **does not** warrant a new normative Discovery policy from one failure.

The highest-value next **separate** discriminator is **same-path/no-PACK strong-control**: for each `.txt` cohort build exactly the same pathname/data tree with standard Builder vs `CMPCT_MICRO_PACK_MAX_FILE=0`, compare real complete CMPCT bytes and reader semantics (then charged create/read costs). Only this controls the crucial path/codec-confound sufficiently to determine whether pack policy itself induces duplicate-file storage regression. Do not tune pack thresholds from O8b data or promote an extension-dependent win as a generic capability.

## Hard product/promotion limits

O8/O8b modify **zero** production source files. The test-only root-level C consumer is not safe arbitrary-root filesystem extraction, retains members in memory, and does not cover symlink/hardlink/mode/path traversal, Windows/macOS, hostile concurrent archive edits, recovery, or actual ecosystem packaging. No release benchmark has been passed as a promotion gate by this result; successful r24 workflow may skip substantive parity. Do not alter frozen original questions/results, shared `docs/discovery/STATE.json` (another PR owner), old benchmark thresholds or historical release identity. Both O8 and O8b results stay independently attributable to their own hosted HEAD; later documentation commits do not retroactively become their tested HEADs.

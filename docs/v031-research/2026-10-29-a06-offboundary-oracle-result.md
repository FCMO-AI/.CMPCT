# A06-O0 — Off-boundary exact-region scientific result (2026-10-29)

**Status:** research-only; **not** a valid CMPCT representation, product improvement, release benchmark, nor general impossibility proof. Scientific prediction is frozen at `c2b4f7efa0f8e7e1fd193c7b3e5de12fd5d1cb88`; this result does not alter the preregistered kill/reopen conditions. The exact current branch and CI evidence must be verified in [PR #760](https://github.com/FCMO-AI/.CMPCT/pull/760) rather than inferred from this time-stamped report.

## Question and context

The Assumption Ledger's A06 asks if physical ownership boundaries can be independent of the original file/chunk boundaries. A16-O2 previously showed that **position-aligned** 4-KiB dedup mostly fails to generalize to complete natural headers. That does not decide **off-position** exact intervals. Rather than adding another decoder path, A06-O0 runs a bounded, content-only anchor detector and prices each discovered copy against strong simpler controls.

This exercise is deliberately distant from the active ownership of Reader/compaction integrity implementation in PRs #569, #741, #749 and #750. It does not edit those surfaces, format/release law, frozen experiments, Discovery STATE, or benchmark thresholds.

## Local measurements (full source files)

Three sets of 32 complete headers, selected prospectively by SHA-256 of path (not by measured compressibility), from installed Linux `/usr/include`, C++ and Boost trees, each file between 2 KiB and 256 KiB. The source-file SHA-256, path and original length for each selected member are in the raw artifact; source versions may differ on another host.

| Cohort | Logical B | Gifted off-boundary exact B | Charged root/literal lower-bound B | Independent Zstd-19 + 16B/member | Solid Zstd-19 |
| --- | ---: | ---: | ---: | ---: | ---: |
| other `.h` | 786,701 | 776 (0.099%) | 149,525 | 149,895 | **130,735** |
| C++ `.h` | 679,399 | 26,888 (3.958%) | 115,401 | 116,395 | **74,169** |
| Boost `.hpp` | 394,562 | 2,069 (0.524%) | 57,868 | 58,425 | **45,734** |

On this host, same-position shared 4-KiB bytes: **0** in all three cohorts. Whole-file duplicate logical bytes: **0**. Exact reconstruction asserted for all 96. One shifted 8-KiB synthetic case passed; three independently seeded random control files yielded zero discovered cross-file matches. The optimistic root/literal candidate saves only 370/994/557 B versus per-member Zstd19, but **loses 18,790/41,232/12,134 B to Zstd19 solid**—approximately 14.4%/55.6%/26.5% larger.

The gifted cross-file coverage describes proposed exact copies **before root ownership selection**. Physical candidate savings are smaller: root files must be stored whole to prevent cycles, with actual copied totals of 776, 13,697 and 1,318 B respectively, and 1, 32 and 6 charged references. A source-file-to-reference decode ratio of **287.7×** was observed on one C++ match; this is a potential selective-read debt, not measured CMPCT read amplification.

## Fully charged versus gifted distinction

The detector uses content-only 64-byte rolling hash anchors, low 9-bit acceptance, at most four previous positions per anchor, byte-for-byte confirmation, 128-byte minimum and 64-KiB maximum extended match, deterministic non-overlap selection. This is **not a complete or optimal matcher**; no-match is not a proof that no exact region exists.

The proposal is charged (optimistically) with one full Zstd19 root for every referenced source file, compressed residual literals, **16 B per COPY** and **16 B per member**. This is favorable to A06: it omits real CMPCT index/framing, persistent SHA/CRC proofs, recovery/failure semantics, runtime CPU/RSS, and any future reader complexity. No archive is produced. Solid Zstd19 has nonselective decode, so it is a size control only; A06 cannot claim a strict Pareto loss without measuring the selective-access benefit.

## Preregistered decision

The all-cohorts-at-most-2%-gifted early-retirement rule does **not** fire because C++ yielded 3.958%. The preservation test (at least one cohort with 10% gifted copy coverage and 3% improvement against independent compressed baseline) also does **not** fire. The honest status is **INSUFFICIENT HEADROOM / INDETERMINATE A06**, with a strong negative economics signal for this particular low-cost detector on complete natural headers. Do not implement A06 in CMPCT based on this O0. Reopen only for a materially different, full-cost structural opportunity or a stronger held-out population, and explicitly compare real CDC/Mosaic controls. No policy self-modification is earned.

## Evidence, controls and limits

**Local independently checked package** (2026-10-29 12:10Z):
`cmpct_a06_o0_research_evidence.zip`, SHA-256 `376c9131d725ba19df5f9e1b72e83f1f69d13dbd40c087a0d5728175bbbf3a7e`.
The package contains the original source manifest for all 96 files, exact copy coordinates, original and updated runner, source-independent auditor and raw repeated checks. Independent auditor reconstructed every target from copied source spans + target literal spans and rejected **2/2 adversarial edits** to source-coordinate and source-file-hash receipts. It does not remeasure CI or prove all representation metadata.

A GitHub-hosted dedicated [A06 scientific workflow](https://github.com/FCMO-AI/.CMPCT/actions/workflows/v031-a06-o0.yml) replays the same structural method on a different host, with source SHA manifest and independent copy-receipt reconstruction. **Host run results are not automatically the same corpus**: installed package versions can change which files are selected. Hosted claims require exact-head job completion and original artifact inspection.

A first hosted run [#40870520648](https://github.com/FCMO-AI/.CMPCT/actions/runs/40870520648) failed at a `ctypes` bytearray type error; its diagnosis and repair were preserved. Another intermediate run #40870731374 completed scientifically before reference receipts were added. The first receipt-bearing run [#40870840225](https://github.com/FCMO-AI/.CMPCT/actions/runs/40870840225) failed because a literal `\\n` was accidentally inserted in Python source by the file-editing tool; repaired in commit `6879b5d673d549b1270970ad8efb7f30e1a043ef`. Neither failure is product evidence. A succeeding independent receipt-bearing exact-head hosted court is **pending until explicitly confirmed**.

Local environment: Linux 6.18.55, glibc 2.41, Python 3.13.5, Zstd CLI 1.5.7; direct libzstd 19 used **consistently** across the size controls. Direct libzstd frame counts can differ slightly from the Zstd CLI; no cross-engine comparison mixes them. This lower-rung test cannot earn current product benchmark credit.

## Counterfactual and next executable target

A simpler prospective signal—zero same-position exact 4KiB matches—would have prematurely rejected the C++ off-boundary 3.958% opportunity, so positional screening is not a logically valid universal A06 oracle. But the **complete compressed-solid control** immediately eliminates the practical case for building this particular detector into product. Future A06 claims should charge strongest alternative representations as early as possible and account for the physical ownership/decode unit. The active product-critical next work belongs to existing Reader/compaction owners: #569 cold-open bounded admission, #749 verified-inode publication, #750 logical SHA semantics and exact-source CI. No shared Discovery STATE mutation in this research branch.

**Publication decision:** no merge, release, version or on-disk-format change; keep the Draft scientific evidence separate from product.

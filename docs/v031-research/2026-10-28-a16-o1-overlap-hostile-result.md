# A16-O1 — Co-owner intersection adversarial result

Date: 2026-10-28 UTC
Status: **FALSIFIER FIRED. Binary globally shared/unique grouping is not a sound unconditional physical-owner boundary policy.**
Preregistration first commit: `6c0a5602dc00fc499f092f4a3f1b89ba534b1b17`.
Implementation: `research/a16_o1_coowner_intersection_hostile.py` after the preregistration.
Inherited research ancestor: A16-O0 PR #683. This work does not edit canonical Builder/Reader, release/format, native core, frozen comparisons or Discovery shared state.

## Distinct failure mechanism

A16-O0 grouped adjacent 4-KiB blocks based on the **same boolean global classification**, shared between two or more members versus unique. A16-O1 asks whether equal classification ensures that the same group of members shares the **concatenation**. It does not. Two parts can each have multiple owners with different owner sets; their concatenation can have one owner. A coalescing algorithm that deduplicates only after the concatenation can destroy the very sharing it attempts to exploit.

The held-out structural generator uses 32 x 64-KiB high-entropy members with 16 independent positions. At each position, it constructs four 4-KiB random candidate blocks and assigns each to exactly eight distinct members, permuted independently by position. Consequently **every atomic chunk is shared by eight members**, but entire member combinations are effectively unique. Neither admission code nor serialized envelopes use the seed/regime labels.

## Measurements: local component, two seeds

Linux x86_64, Python 3.13.5, libzstd and independent Zstd CLI 1.5.7, same source members and Zstd-19 in both candidates; per-owner and per-member SHA-256 and complete headers/references counted. All source members reconstruct exactly in an independent wire-parser/CLI decoder.

| Seed | Direct member frames | Strong fixed 4-KiB CHUNKREF | Binary sharing-class SEGREF | SEGREF / CHUNKREF |
| --- | ---: | ---: | ---: | ---: |
| 20261030 | 2,098,764 B | **267,340 B** | 2,100,044 B | **7.85533×** |
| 20261031 | 2,098,764 B | **267,340 B** | 2,100,044 B | **7.85533×** |

The fixed-chunk control uses 64 physically unique blocks across all 32 members. It retains 16 references/member. SEGREF joins all 16 consecutive 'shared' blocks into one 64-KiB owner/member, yielding 32 effectively unique 64-KiB physical owners and **7.855×** more bytes. This exceeds the preregistered 5.0× falsification target in both independent seeds. Exactly **192** decoded member outputs were independently reconstructed across 2 seeds × 3 representations × 32 members, SHA matched and no bytes were lost.

## Decision-changing negative

Combined with A16-O0's stricter-comparator primary miss (0.9768% byte savings versus a locked 1% threshold), this adversary demonstrates the **binary sharing-class heuristic is a saturated research hypothesis for unconditional promotion**, notwithstanding its measured 3.9× synthetic full-member decoder-component benefit in the tidy shared-prefix regime. A default portfolio can fall back to the much smaller fixed owner representation for this case, but *the act of discovering both arms and building both has nonzero create/search cost*, and the experiment has not justified paying it globally. A genuinely new hypothesis would need co-owner **intersection-aware** segmentation, explicit work/memory accounting, and prospective generic admission; it does not inherit a win from A16-O0.

No installed CMPCT v0.31 Reader, open/read-range/RSS/recovery/portability gate or official 1.0 competitor benchmark was executed. The hosted CI court on PR #683 now contains both A16-O0 and O1 and must be assessed at its exact HEAD separately from these local observations.

## Counterfactual discriminator / learning

A pre-implementation **set-intersection test on adjacent blocks** would have exposed this entire risk: global sharedness is not transitive to a shared concatenation. Because it can kill the naïve class rule without writing any product code, it is a cheaper falsifier than running a full product benchmark. Keep this as a prospective scoped lesson, not a justification for changing normative Discovery Engine policy on one observation.

Outcome: `RETIRE_UNCONDITIONAL_BINARY_COALESCENCE`. Preserve bounded run-coalescence as research, not product; no merge or release.

## Source-exact hosted replication (later evidence, not merged product)

The dedicated science workflow [run #40714118283](https://github.com/FCMO-AI/.CMPCT/actions/runs/40714118283) completed **SUCCESS** on its exact tested source HEAD `07cd03b598022371ce57d5306c67bf1799245eda`. Both Ubuntu 22.04 and Ubuntu 24.04 jobs passed preregistered A16-O0 byte/exactness, A16-O1 co-owner overlap and six hostile-envelope refusal checks, then uploaded raw JSON receipts. This replication supports research-only wire exactness and structural amplification, **not** Linux/macOS/Windows installed CMPCT performance. Initial generic Engineering Evidence on the same source HEAD failed on missing formally named PR dossier headings; the PR body was corrected without changing the evaluator. This documentation-only follow-up changes source HEAD and requires fresh exact-head CI before any full-green claim; no merge/release authority is inferred.

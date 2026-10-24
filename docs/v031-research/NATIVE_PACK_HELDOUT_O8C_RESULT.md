# Native S_PACK — O8c exact same-path complete-product result

Date: 2026-10-24 UTC. **DECISION: EXACT DUPLICATE MICRO-PACK STORED-BYTE LOSS CONFIRMED; OTHER COHORTS FAVOR DEFAULT POLICY; OPT-IN NATIVE GROUPING PRODUCTIZATION STILL PENDING.** This is scientific and product-consumer evidence, not a release promotion.

## Immutable experiment identity

- Prospective question frozen BEFORE implementation in `docs/v031-research/NATIVE_PACK_HELDOUT_O8C_PREREG.md` at commit `cd77f1835273b2334d0f247895b8459a1f284df7`. Original O8/O8b questions, data and evidence remain unchanged.
- Exact unchanged product/native/C-source ancestor: PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae`. Current O8c test-only implementation on branch at SHA `f2e6b81fcc932ead4d16cfb8537ca17c2c077dd2`.
- Hosted [Actions run 40066944189](https://github.com/FCMO-AI/.CMPCT/actions/runs/40066944189): **SUCCESS**, all C result checks executed, same-path data; artifact **12549219834** ZIP SHA256 `5ae94be7c86d874e7970b3da4d87ca5d1d991242bec82d5f50acc3a7f6de94d1`; `result.json` SHA256 `b9526bd4e8c23bb9959980b891310293bd3101244f49666c00fcf74341cd71db`. Independently downloaded, ZIP tested and raw sample counts/hash manifest cross-checked.
- **64 full Builder builds and 128 complete native public-C archive extractions**, all 128 rebuilt directory name/content SHA sets correct. Four content families × two pack-policy configurations, four alternating ABBA blocks, eight genuine builds per configuration. Each reproducible same-config archive was byte-identical across its eight builds, and each source remained immutable. Same .txt path names/payloads within a policy pair, including same `.bin` noise member in mixed case.
- **Normal** = unchanged standard Builder; **no-pack control** = exact same Builder with inherited `CMPCT_MICRO_PACK_MAX_FILE=0`. This changes the Builder's ability to micro-pack, allowing other pre-existing policy behavior to adapt; measures complete alternative product economics, not one isolated codec routine.

## Direct paired results

| Same exact logical tree | Normal archive B | No-pack B | Normal minus no-pack B | Normal create wall ms | No-pack create wall ms | Normal grouped-C extract ms | No-pack grouped-C extract ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Related 256 × 768B | 4,505 | 32,041 | **-27,536 (-85.94%)** | 15.386 | 55.292 | 9.968 | 13.008 |
| Independent 256 × 768B | 199,562 | 225,870 | **-26,308 (-11.65%)** | 18.236 | 127.114 | 9.824 | 17.330 |
| Duplicates 256 × 768B | 1,491 | 1,422 | **+69 (+4.85%)** | 7.699 | 7.506 | 9.392 | 10.848 |
| Mixed 256 + 70KB | 172,651 | 200,608 | **-27,957 (-13.94%)** | 18.649 | 113.937 | 10.645 | 17.557 |

Elapsed times include complete Builder calls and native C-process archive open, exact read, group admission, filesystem writes. Native extraction wall medians are from 8 repeated C child processes per mode/config; all inherited C ABI code unchanged. Full archive bytes include physical blobs, headers and indexes, not an optimistic payload oracle. CPU medians are also in the immutable artifact (example related normal 15.393ms create CPU vs no-pack 55.239ms). Whole-process RSS medians are not proof of zero peak incremental memory. Neither archive policy universally dominates: **duplicates default saves ~1.455 ms of grouped extraction vs no-pack but costs +69 stored bytes**, and create times are close enough that a broad speed conclusion is not earned.

## Critical science and attribution limits

1. Duplicate-content byte debt is now a **real same-path, same-content, complete-archive** result: default PACK 1,491B vs stronger actual no-PACK control 1,422B. Unlike O8b .txt/.dat, no filename identity confound remains. This is a **local synthetic workload loss**, not evidence of failing the frozen release matrix.
2. The independent high-entropy `.txt` archive showed **zero Zstd native-batch eligibility in O8b/O8c**, while default packing saved 26,308 bytes vs no-pack. This does **not** necessarily imply zero physical PACKs! The native owner query supports only compressed Zstd PACK, while Builder may choose physical RAW PACK for incompressible grouped bytes, leaving localized individual reads. Physical RAW vs separate-blob ownership has **not yet been independently inspected on this exact artifact**, so treat that explanation as source-consistent, not a measured codec disposition. Do not call zero native batching zero Builder packing.
3. Any cost explanation based solely on extension is too narrow: O8b showed `.dat` and `.txt` produce different bytes due to whole Builder policy. O8c's exact same-name control is stronger and resolves stored-byte direction, but does not isolate decoder CPU, dictionary selection or transient allocations inside Builder.
4. Aggressive blanket policy changes are unjustified: only duplicates show local 69B loss; related/mixed and even independent-content cases gain material storage and create-time efficiency. The bounded optimization question is generic admission of single-distinct-member PACK and shared-duplicate identity, not a blanket switch to no-PACK.

## Mechanisms, counterfactuals and next executable decision

- O8 (96 reconstruction controls) failed to exercise batch at all because .dat suffixes were not in the Builder text-hint set; valid negative admission control.
- O8b (128 reconstructions) varied only suffix, confirmed three .txt cohorts with batch and one with no native Zstd batch, 9.09×/9.43× wall improvements for related/mixed; but could not attribute archive-size differences fairly due to renamed paths.
- O8c (64 full builds, 128 native extractions) varied only existing micro-PACK enablement on identical .txt trees. This controlled direct-base result establishes the real *stored-byte cost* and tradeoff.
- Cheapest next discriminator: independently inventory actual physical PACK codec/unique-content ownership of related, independent and duplicate archives; then test one **generically recognizable single-unique-content cohort** admission rule versus exact unchanged default and no-pack Builder on held-out corpus. Do not implement based on a single .txt/duplicate fixture; price full archive, create, RSS, selective work and memory, maintain fallback.
- Do not substitute O8c for an actual secure filesystem extractor; original public C consumer refuses nested paths and does not handle arbitrary inode/link metadata, hostile destinations or multi-platform packages. No native/format/release changes, no Bounded Drift interference, no Discovery STATE overwrite, no promotion credit or comparator changes.

This result file is append-only scientific evidence for O8c and does not retroactively change any preregistration, exact-head run or immutable old results.

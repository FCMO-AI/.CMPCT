# J24C02 / J24C02b — source-exact four-way Reader and measured fixed-chunk open-cost debt

**Date:** 2026-10-27 UTC. **Status:** narrow product correctness candidate + **material performance negative**. Released CMPCT v0.30.0 and wire revision 24 unchanged. **No merge or release.**

## Provenance / preregistration

- Product source base: #567 exact `d3b12852511095d6e98803f55cfd700b8e9ac6b3`, original Reader blob `930f90478a45201617e675e3d9bd0eb9b7c70f53`.
- O215 owner source: #568 at `3aad965da3b81eb47257e974e1bd86a21add45da`, Reader blob `73e4bfdab49af8c3302a313793ed594a8272b51d`.
- J24C02 prereg: `3c4f4a5ab9567331e6fdf687ed5a4af30ccb07a1`, before source mutation `2d2e5cd754af4a445c41c444c6a0299aa4c769be`.
- Separate prospective **cost** prereg J24C02b: `f7c34513f5996aba85de5bc3828d8fad37148d73`, before cost instrument `6339df22197a4b83d28969a9b9c27b17d1176b4f`.
- Result-bearing source HEAD: `6f228978c592402dbb77cddfe08add538e50bdc1`. Candidate Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de4405166`.
- Source intervention is strictly the complete O215 `CMPCT.__init__`; every byte outside that constructor equals J24C01. The original `src/cmpct/validation.py` and unmodified O212/O214/J24W02/O215 courts are retained. O215 original test and causal baseline probe blobs `a8efaebd9fff8b3203cfd55304d365c309ff394b` and `7707f2f0f5431bde3786b0d293175071d72d2c9e`.

## Source-exact product correctness

- [J24C02 exact-head push CI #40450074731](https://github.com/FCMO-AI/.CMPCT/actions/runs/40450074731) and [PR CI #40450078072](https://github.com/FCMO-AI/.CMPCT/actions/runs/40450078072) both **SUCCESS on Ubuntu 24.04, macOS 14 and Windows 2022**.
- Each host independently installed the actual candidate; verifies source blob identity, executes **45 pytest PASS + 9 subtests PASS** (O215 12 + inherited O212/O214 25 + W02 8), including frozen independent r24 fixed-chunk vector, valid repeated references, zero-length member, authenticated hostile size/ref variants, original Windows absent-fchmod behavior.
- Linux re-installs original #567 Reader as a control and confirms the authenticated five-declared/four-physical S_CHUNKS file permits **in-bounds short selective read**, whereas original full `read()`/`verify()` already reject. Composed Reader rejects at open before mmap; no post-verification corruption claim.
- Linux additionally preserves J24F11 fd-bound fresh S_CHUNKS/S_CDC inode publication, J24F12 write/search-only parent, and integrated genuine valid/malformed CDC × fd-publication courts. All PASS.
- No changed Builder, codec, format, original validator, release tests, thresholds, performance comparators or historic results.

## **J24C02b: material cold-open performance regression confirmed**

[Run #40450074731, Linux original result artifact 12710016662](https://github.com/FCMO-AI/.CMPCT/actions/runs/40450074731/artifacts/12710016662). GitHub provider ZIP SHA-256 `4693251971225ae15ad0f9369fbddf76f3e6dabe0960fbc756a7a97455cd7313`.

**The same complete authenticated r24 archive bytes** are opened by the authentic original #567 and candidate #569 Readers installed separately on one Ubuntu 24.04 host; separate-process measurements exclude import/startup from timed sections. Five real constructor-open-and-close samples per subprocess; three ABBA cycles with two subprocesses per arm per cycle. All raw results are retained in `cold-open-abba.json` inside the artifact, not just headline medians. Numbers below are median-of-per-process medians, original in milliseconds. Linux `ru_maxrss` is *absolute peak process RSS* (not incremental) and must not be interpreted as full product memory credit.

| Authenticated fixed-chunk refs (one physical 4-byte RAW blob) | Complete CMPCT file bytes | #567 open wall ms | #569 open wall ms | Candidate/base wall | Parent CPU ms | Candidate CPU ms | Process peak RSS KiB both |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 452 | 0.0667 | 0.0788 | 1.182× | 0.0672 | 0.0794 | 24,348 |
| 4,096 | 474 | 0.1069 | 1.7252 | **16.136×** | 0.1075 | 1.7251 | 24,604 |
| 65,536 | 482 | 0.9736 | 26.5335 | **27.253×** | 0.9749 | 26.5275 | 27,036 |
| 262,144 | 516 | 3.7102 | 105.7588 | **28.505×** | 3.7116 | 105.7544 | 34,052 |

**Prospective material-debt discriminator fires** at 65,536 (+25.56 ms, 27.25×) and 262,144 (+102.05 ms, 28.51×), well beyond both the required ×2 and absolute +5/+20 ms conditions. The validator does O(references) interpreted Python checks on an extremely compressible but structurally valid index. This is a substantial new **cold-open / tiny-archive amplification** cost on an adversarial high-reference representation, not a measured general mixed filesystem cost. High-reference repetition is a legitimate r24 storage shape but has not been demonstrated to be produced at this scale by canonical Builder.

**Independent artifact audit:** the downloaded provider ZIP was opened outside Actions; all four fixture ref/logical-length values, four archive sizes, 12 subprocess observations per fixture, 5 wall/CPU samples per subprocess, 3 ABBA cycles, original/candidate Reader source SHA identities, recorded medians, ratios, and prospective debt predicate were recomputed from JSON. Result: `AUDIT_PASS=ALL_4_SAME_INPUT_12_PROCESS_RAW_COURTS_INDEPENDENT_MEDIAN_REPLAY`. No data reclassification or omitted losing case.

### Interpretation and alternatives

- The **correctness hypothesis survives**. The **unqualified integration/promotion hypothesis fails** due to measured cold-open tax. A green specialized court cannot waive this debt.
- Strongest simpler control is the exact same Reader without added strict S_CHUNKS scan, under the identical file. Source has identical other Reader methods, so the extra loop is causally credible; an independently profiled per-operation allocation/call attribution is still missing.
- A robust alternative must retain complete authenticated same-effective-index geometry checking while reducing Python-per-reference work or amortizing it through a bounded prepared map/native admission representation; any data-dependent shortcut needs hostile type/bool/invalid references, repeated physical indices, overflow, latest generation and held-out shapes. Avoid skipping checks for large counts, benchmarking away malicious inputs, or weakening resource bounds.
- Treat this as an explicit blocker for unconditional product promotion, **not** a reason to revert a proven vulnerability correction, nor a license to relax release parity or to create a parallel unreviewed Reader.
- The existing-target publication race issue #528, mutable mmap source/truncation, Windows/macOS fd publication parity, full 4GiB ZIP64, recovery and general release gates remain independent open debt.

## CI and next action

The exact result-bearing source `6f228978...` has two specialized 3/3 green workflows. Engineering Evidence corrected by complete PR body; full native/fuzz/general CI must be classified by exact final head separately, and official substantive release-parity has **not** been earned. Old J24F04/J24F05/J24F09 source-pinned historical workflows may fail at historical blob identity before behavioral tests; do not relabel them as product regressions or modify them to invent green.

**Decision:** preserve and hand off J24C02 as a four-way strict-correctness candidate with explicit **material cold-open regression debt**. Do **not merge, release or claim broad performance improvement**. Highest-value bounded next experiment: profile the actual validator's dominant interpreted reference checks and test a meaningfully different bounded/native or proved prepared-geometry admission mechanism on identical original and held-out full Reader opens, preserving all O212/O214/O215/J24F11/F12/W02 hostile and positive controls. Coordinate owners #567/#568.

Discovery policy and `docs/discovery/STATE.json` unchanged. No version or format changes.
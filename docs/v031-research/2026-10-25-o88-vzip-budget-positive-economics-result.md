# O88 result — 64 MiB VZIP absolute resource admission versus genuine O63

**Date:** 2026-10-25 UTC. **Scientific decision:** `NO_SHARED_SIZE_DEBT_ON_TESTED_FAMILY` / narrow positive-budget-loss hypothesis **FALSIFIED** for these three source-bound cohorts. **Research-only:** not a product release, not a new global threshold, not universal VZIP dominance. Frozen pre-result [O88 preregistration](2026-10-25-o88-vzip-budget-positive-economics-prereg.md) at `f8a3f1f3b3597a42dae1246198ccc49a707e0434` remains unchanged.

## Problem and baseline

O86 #444 introduced a default 64 MiB cumulative declared-member output limit to optional VZIP exploration; over-budget ZIPs are stored as ordinary exact opaque data. Since O71 #427 previously measured meaningful complete archive savings for some high-inflation, 1 MiB **shared** mixed-entropy ZIP cohorts, O88 prospectively asked whether O86 could lose those savings at 65 MiB despite large resource work avoided. A global ratio-only rule was already falsified; an absolute resource budget is a different policy.

## Exact actual source and hosted evidence

Original **O63** `18e32cae012f5dca9fc47f10d194f8b81005c85c` — Builder blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`, codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`.

Candidate **O86** `6225e30f3e21c0783aa56726b52a3a3583540f99` — Builder blob `e46c8670c11c386925f9ae228b25de44c8045f2e`, codec blob `7d4c4a5a5f00c42561043611e5d4400dd8af38e6`.

**Complete successful hosted run:** [GitHub Actions #40206269074](https://github.com/FCMO-AI/.CMPCT/actions/runs/40206269074) at exact executable research HEAD **`e126a33654210b81021408d16cff7f04fffc7620`**, artifact [#12603981620](https://github.com/FCMO-AI/.CMPCT/actions/runs/40206269074/artifacts/12603981620), GitHub artifact digest `sha256:430dbbd9091df59d56994ed79b8bd9f69a97a27f6c4b2ace996cebdf4df3c9f3`, raw `o88-raw.json` SHA-256 `41e91ffb7f3573633d275f29b8d2e756d6a463a4f91a693f3b7e2ac12ae54ae9`.

One earlier experiment [#40205916758](https://github.com/FCMO-AI/.CMPCT/actions/runs/40205916758) ran source-identical low and shared-high cohorts and preserved valid raw measurements but **failed at the research instrument** because its top-level orchestrator referenced `S_BLOB` outside scope. It was not a product failure. The only patch from first to successful instrument replaces that undefined constant with canonical r24 storage-kind value `0` in the assertion; no product source or functional evaluator semantics were modified. Partial original artifact [#12603947242](https://github.com/FCMO-AI/.CMPCT/actions/runs/40205916758/artifacts/12603947242) retains its original negative and values. The successful run supersedes it for the final decision.

**Execution contract:** genuine independently installed original and candidate `site-packages` instances, exact Git blob checks before and after independent install, three real ZIP files per cohort using Deflate levels 1/6/9 and deterministic metadata, **three fresh-child AB/BA repetitions per arm per cohort = 18 completed whole-Builder observations**. Builder timers exclude interpreter startup; raw data captures create CPU/wall, process peak RSS, verify/read/extract wall/CPU, complete stored bytes and SHA, storage kinds and original source SHA. Same physical source per A/B in each cohort; different cohorts and independent runs are not treated as identical physical inputs. Extracted physical ZIP bytes match original SHA in all observations.

## Direct numeric results (Ubuntu 24.04, successful hosted run)

| Cohort | O63 full CMPCT B | O86 full CMPCT B | O86 − O63 stored B | O63 create CPU median ms | O86 create CPU median ms | O63 peak process RSS median KiB | O86 peak process RSS median KiB | Storage modes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 MiB per ZIP, shared expanded content | **18,344** | **18,344** | **0** | 31.099 | 31.790 | 30,272 | 29,736 | Both VZIP (2) |
| 65 MiB per ZIP, shared expanded content | 664,428 | **52,641** | **−611,787** | 1,325.164 | **8.721** | 304,688 | 300,676 | O63 VZIP (2); O86 opaque (0) |
| 65 MiB per ZIP, independent expanded content | 913,287 | **52,567** | **−860,720** | 1,376.148 | **8.412** | 371,304 | 300,948 | O63 VZIP (2); O86 opaque (0) |

The O86 guard on these above-budget cohorts produced **92.08%** and **94.24%** smaller complete CMPCT archives respectively than original O63, and approximately **152×** and **164×** lower measured creation CPU; these are **within-run ratios on these synthetic Linux cohorts only**, not general performance claims or official release-gate credits. Under-budget O63/O86 archive SHA and bytes remained identical. Actual `CMPCT.verify`, `CMPCT.read`, `CMPCT.extractall(metadata=False)` returned the original ZIP bytes in every observation.

The first source-exact hosted run, though ending in a research-script NameError, independently reproduced byte identity at 1 MiB and the same **664,428 B vs 52,641 B** complete archive sizes for the 65 MiB shared family, with three records per engine and matched original source SHA. Absolute times varied across hosted runs: original O63 shared-high CPU 725.508 ms vs 1,325.164 ms on the next run. Such cross-run timing variation is not treated as product regression or reproducible absolute timing.

## Decision: negative result is valuable

The preregistered conjecture that 65 MiB high-ratio *shared* mixed data would cause a complete-byte loss from O86's 64 MiB absolute budget **did not survive**. Historical O63 genuinely emitted VZIP for all three ZIP files; nevertheless its output was substantially **larger** than the O86 exact opaque alternative on this family. Repeated shared raw content is **not sufficient** to guarantee VZIP complete-byte superiority at another size regime. The O71 1 MiB structural win cannot be extrapolated by inflation ratio or shared plaintext identity to 65 MiB. No new threshold should be fitted to these cases.

This narrows—but does **not** prove absence of—other above-budget positive cases. The O86 guard is still a resource-admission mechanism, not a complete economic predictor. Stronger possible positive families may require actual metadata/container diversity, different redundancy organization, or non-Deflate objects. Proving those would require a new prospective question, not renaming/tuning O88.

## Alternatives considered

The stronger simpler control was exact original O63, rather than a patched `make_vzip_recipe` in a candidate subprocess. A gifted opaque-only oracle could estimate bytes faster, but would not establish the original engine's real resource cost. A full frozen release matrix is too costly before this targeted binary fork. The O71 ratio-only negative precludes ratio gardening; the absolute budget remains a bounded search limit without any new selector.

## Losses, ambiguity and negative evidence

The test trees are deliberately patterned with repeated long runs and fixed small random tails. Their internal Deflate streams themselves are unusually compressible under CMPCT's generic opaque path; this may explain why original O63's VZIP recipe loses so badly at 65 MiB, but there is **no profiler-level attribution** of the stored-byte owner. The size result is exact; do not claim a universal cost curve or that 64 MiB is an optimal cutoff.

Process peak RSS does **not** fall proportionally to speculative CPU reduction. On shared-high it changed only 304,688 → 300,676 KiB, demonstrating substantial independently held source/input memory. On independent-high RSS changed 371,304 → 300,948 KiB. The 64 MiB cap is not a whole-Builder RSS cap. The genuine source O63 and O86 matched each other below budget, but no Windows/macOS economic controls and no official same-runner direct v0.30 release benchmark were executed. O86's separate three-platform functional court #444 does not imply these ratios transfer to other operating systems.

## Safety, integrity and resource accounting

All original physical ZIP bytes were read and authenticated by SHA before/after each operation and after `verify/read/extract`; no weakening or rewriting of archive records or Reader semantics. Hostile corruption, source mutation mid-capture, ZIP resource declarations that lie, out-of-root filesystem pivots, atomic output publication and reader memory bounds remain independently owned problems. User data and private files were not used.

## Compatibility and portability

No product implementation, format revision, codec ABI, Reader, Writer, native core, release policy, frozen benchmark or source guard was modified. Research experiments are Linux-only; O86's original three-platform basic functional suite remains a separate claim. Metadata restoration under Windows is not claimed by this `metadata=False` byte-equality court.

## Performance accounting

18 genuine installed observations (3 cohorts × 2 historical engines × 3 fresh processes); create wall/CPU; final complete bytes/SHA; maximum-process RSS and Reader verify/read/extract retained in raw per-run JSON. Timers exclude interpreter startup, though RSS reflects whole child lifetime. No kernel/cold-cache control and no full frozen release comparator. Reported savings are exact within tested source and host and not release credit. Effective default O86 policy is measured, not tuned.

## Public-surface check

All fixtures are synthetic, seeded, deterministic, project-specific, and public-safe. No credentials, unrelated private provenance, confidential corpus identities or customer data.

## Completion gates

- [x] Preregister before instrument; source hashes fixed.
- [x] Actual original O63 and O86 installed without fake substituted original implementation.
- [x] Exact source SHA, complete archive B/SHA, original ZIP reconstructability, positive low-budget identity and over-budget correct fallback.
- [x] Three AB/BA repetitions per engine and case; 18 completed observations, no skips.
- [x] Preserve original failed instrument run and negative outcomes; successful rerun.
- [ ] Official frozen size/CPU/extract release parity and broader portable/mutable/hostile resource economics; not attempted and **not implied**.

## Future leverage and counterfactual

A single original-O63-versus-O86 above-budget complete-archive A/B on actual previously favored mixed shared content resolves the initially uncertain loss hypothesis at a much lower cost than a full release matrix. The earliest portable discriminator is not inflation ratio but the **complete stored bytes and work after physical compressed-stream reuse is charged**. No discovery-policy mutation is earned from one experiment. The next nonduplicate target is to integrate O86 on its owner branch only after checking other bounded positive structural controls, with costs quantified under current final-form product semantics; the simpler baseline is allowed to win.

**Scientific verdict: O88 negative for above-budget size-debt hypothesis; positive evidence for O86's bounded exact opaque fallback in these 3 source-bound families; no release/product-promotion credit.**

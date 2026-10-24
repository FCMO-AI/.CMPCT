# O8b preregistration — exact extension-admission falsifier and corrected PACK-heldout probe

**Date:** 2026-10-24 UTC. **STATUS: NEW PROSPECTIVE EXPERIMENT BEFORE SOURCE CHANGE.** Original O8 preregistration and its executed result MUST remain immutable. Parent exact code: PR #330 at `a1af021d6b91c450079356b2b35862defc2d7f4d`; inherited native/C product source PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae`.

## Decision-changing negative that motivates this DIFFERENT experiment

Original O8 hosted [run 40066222077](https://github.com/FCMO-AI/.CMPCT/actions/runs/40066222077), artifact 12549077739, successfully executed 96 byte-exact extractions across six cohorts, but **0/6 cohorts were admitted to a native PACK batch**. The script generated files with `.dat` extension. Direct source audit identified `src/cmpct/builder.py::_build_micro_packs()` which requires `any(x in TEXT_EXT for x in c.hints)`; `.dat` is not a text extension. Therefore O8's related-content cohorts **did not interrogate the hypothesized batch speedup at all**. It legitimately measures near-zero fallback overhead only. This is an **instrument design confound**, not a falsification of batching. Do NOT retrofit its frozen prereg or claim six held-out batch workloads.

## New primary question

Given identical source payload bytes and equal-length root-level member names, does changing only the extension `.dat`→`.txt` cause genuine PACK admission, and how do storage bytes, fully verified native C grouped-versus-serial CPU/wall/RSS and fallbacks respond across three distinct content relations?

## Prospective 2×2×3 extension/content control

For each content family (`related_256`, `independent_256`, `duplicates_256`, `mixed_256`) build two real revision-24 archives from exactly the same content payload multiset: root-level `.dat` versus equal-length `.txt` names. The independent large 70KiB `.bin` member in `mixed_256` remains unchanged. Content generation reuses O8 frozen deterministic `population()`; **only last three filename-extension bytes change**. Assert equal content multiset/hash and source member count across extension twins before Builder. No changes to underlying Builder or codec, thresholds, standard TEXT_EXT registry or synthetic source contents.

Eight frozen extension/cohort cells; each archive built ONCE with the real `Builder(workers=1,reproducible=True)`. Four alternating ABBA blocks / 16 fresh-process C-consumer extractions per cell (128 total). Both modes and both extension cells individually check every file hash and name and source archive SHA after every execution. Record complete stored archive bytes, compression ratio, eligible batch/member counts, fallback counts, wall, child CPU and RSS for each of the eight cells. Each .txt/.dat pair shares exact payload lengths/data but cannot have identical filesystem name semantics; record that as a comparison limit rather than calling it formal release-parity.

## Prediction / disproof / decision

1. `.dat` twins should replicate zero batch admission; if not, code hypothesis about TEXT_EXT is falsified.
2. `.txt` should admit at least the high-cardinality `related_256` source and produce nonzero batched members; absence would demonstrate that extension alone is insufficient and demands deeper Builder-policy accounting.
3. `independent_256.txt` and `duplicates_256.txt` are adversarial economics: Zstd PACK admission may not improve stored bytes or may add decoding work, while native batching can amortize repeated reads. No positive speedup assumed.
4. A source mismatch, archive mutation, corrupted output, invalid group/fallback census, or lost independent control invalidates the cell. No corpus selection/tuning after result. Do not convert an experiment success into a generic product performance claim.
5. A material extension-conditioned archive-size loss (>1% of direct `.dat` control) is explicitly recorded as storage carrying cost; a batching speedup does not erase it. Ratio comparison is attribution research, not formal same-path release proof.
6. Classify O8 as `FALLBACK_ONLY_SCIENTIFIC_CONTROL` and O8b as the actual `EXTENSION_DEPENDENCE_DISCOVERY`. Distinguish product evidence, research economics and planned future work. Independent product fix, native safe extractor, arbitrary fs semantics, platform gate and release promotion remain out of scope.

## Cheapest counterfactual discriminator

One `Builder` lookup of `_build_micro_packs` plus the file suffix comparison would have identified the uninformative O8 .dat cohorts **before** execution. General research lesson: any admission-dependent benchmark must independently assert the admission actually occurred, and preserve an explicit no-admission negative. This is a prospective local test-design improvement, NOT a normative Discovery Engine policy change.

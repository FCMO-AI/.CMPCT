# CMPCT v0.31 — VZIP journal O1 hosted product-mechanism result

**Date:** 2026-10-23 UTC. **Evidence tier:** genuine Builder/Reader diagnostic on controlled ZIP-rich inputs, NOT the release promotion or frozen benchmark matrix. **Decision:** DECISION-CHANGING POSITIVE for rejected speculative ZIP ownership, success-path neutral within limited resolution; global productization remains pending.

## Exact provenance
- Independent preregistration: `benchmarks/history/2026-10-23-v031-vzip-journal-zip-heavy-cost-o1-prereg.md` first committed at `b9d8e011f0fb1f1fe4e7656a613f2be96a6a275d`, before executable or results.
- Hosted exact-source run: [GitHub Actions 40027718949](https://github.com/FCMO-AI/.CMPCT/actions/runs/40027718949) **SUCCESS**, job `120667988943`, source `e495117b729b5300f0ecdc68370af001e8bc863d`.
- Original JSON observations, environment/base-native receipt: [artifact 12533376979](https://github.com/FCMO-AI/.CMPCT/actions/runs/40027718949/artifacts/12533376979), artifact ZIP digest `sha256:e9eaf2e5ed39aef72b48e9140ab31d59943fb3f7474507247181dc99d50733d7` (GitHub-reported).
- Immutable base product source: `369255f63aaa6a9c5c5c03eae2d57f8d1776662e`, Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Candidate composed product source: O1 `e495117b729b5300f0ecdc68370af001e8bc863d`, Builder blob `745b05ded92bbf84a681a4b159ac7a3c341858c5`. Both Readers identical blob `c548a2ae4d650e928eb46ed1c2431423e49765b5`. PR #288 keeps this owner implementation byte-identical.
- Branch-script Git blob `1792bc711c38fcfc2d01f80bf06cb8b19409a414`; branch-only workflow blob `0bf444f1bd0cff62e90e49ac700288cf46bdcf9c`. No modifications to released sources or to parent owners.

## Host experiment and exact admissibility
Each regime creates one deterministic input tree with 192 unique 384-byte ZIP_STORED members and one valid compressed final member (193 total). First 0 or 64 ZIP members alias already-scan-reachable loose `.bin` files. Successful final stream uses stdlib DEFLATE; rejected final stream uses valid RFC1951 Z_FIXED which cannot be reproduced by the original recipe-level search. Each child independently checks the exact final stream regime via `deflate_level_for`, exact source tree SHA, `CMPCT.verify()`, complete nested ZIP bytes, and first loose-file identity where relevant. Builds use reproducible mode and one worker, same installed dependencies/native provenance, *fresh child process per observation*, and library create timing excludes interpreter startup. Three ABBA rounds per regime = **6 candidate and 6 base observations per regime**, 36 total source-builds.

| Regime | Base archive | Candidate archive | Complete bytes delta | Base create median | Candidate create median | Median wall delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Successful VZIP / 64 prior aliases | 93,205 B | 93,205 B | **0 B** | 20.353 ms | 20.573 ms | +0.220 ms (+1.08%; ambiguous) |
| Late rejected VZIP / 0 prior | 165,284 B | 78,232 B | **−87,052 B (−52.67%)** | 20.653 ms | 11.844 ms | −8.809 ms (−42.65%) |
| Late rejected VZIP / 64 prior aliases | 165,768 B | 107,774 B | **−57,994 B (−34.99%)** | 22.630 ms | 17.179 ms | −5.451 ms (−24.09%) |

Additional CPU medians match the approximate wall direction in each regime; see raw JSON. Maximum whole-process `ru_maxrss` (KiB): successful base 27,736 / candidate 27,972; rejected with 0 aliases base 26,076 / candidate 25,936; rejected with 64 aliases base 26,384 / candidate 26,132. This **is not incremental Builder RSS** and the hundreds-of-KiB differences are not decision-quality evidence.

## Causal interpretation and negative
The original Builder included speculative candidates discovered while probing valid but eventually rejected ZIP member streams. Even when the final ZIP fell back to opaque storage, their physical encoding remained in the archive. The owner journal removes those rejected objects and restores prior candidate metadata. On these two held-out late-rejection inputs, this is a **strict complete-artifact size win**, not a fixture-name threshold change, and the smaller physical encoding also reduced create wall/CPU. In a successful ZIP, original and repaired archives were byte-identical, consistent with preserving canonical success semantics.

The earlier **synthetic callback-only** source-semantic microstudy suggested nonzero journal bookkeeping (+1.07–1.79× on tiny hash operations). O1 demonstrated that this is not a valid standalone predictor of whole-product cost: avoiding speculative blob encoding can dominate the overhead on actual rejected ZIP containers. This does **not** retire the overhead concern for large successful candidate cohorts; successful-case +0.22ms is small and ambiguous in this six-sample resolution.

## Counterfactual and next discriminator
The earlier actionable cheap signal was **complete emitted archive bytes after a rejected late ZIP compared to a forced-opaque control**, rather than pre/post candidate dictionary cardinality or purely callback microtiming. That signal exposes a root ownership defect earlier and transfers to other speculative representations. Next highest-value action is to read PR #288's **official exact-head general Tests and same-runner r24/ZIP ABBA**, inspect complete actual benchmark artifacts, then decide whether to carry Builder journal into next integration. Only if a high-fanout legitimate successful ZIP proves expensive under real product workloads should there be a further tuned admission/ownership experiment. No change to Discovery Engine policy warranted from one O1 run.

## Boundaries
Source tree is deterministic synthetic ZIP-rich **held-out**, not an arbitrary-filesystem/product benchmark matrix. Input fingerprint is checked per subprocess, and independent ZIP reader plus CMPCT verify ensures exactness; no complete Windows/macOS/ARM platform proof, concurrency mutations, crash recovery or hostile resource ceiling. Archive-size win in rejected cases does not establish general compression superiority versus ZIP/Zstd. Library create medians are not process startup time; single shared runner and 6 observations per side per regime cannot prove small timing differences. Full distributed release record, zero-byte parity, official ABBA timing gates, authentication semantics and legitimate merge authority remain binding.

**No product merge/release, format bump, frozen evaluator weakening, performance threshold change, stale Discovery cache overwrite or new authority asserted.**

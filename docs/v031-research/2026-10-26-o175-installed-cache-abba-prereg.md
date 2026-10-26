# O175 — source-exact installed Reader cache vs historical release, real r24 corpus (preregistration)

2026-10-26 UTC. **PROSPECTIVE: recorded before any O175 experimental implementation/result.** Public v0.30.0 / revision 24 remains frozen. Baseline immutable canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, historical Reader Git blob `e716233403dabd0966863c45635e18fa6afb8`? **Authoritative exact blob is `e716233403dabd0966863c45635e18fa6afb8` only if verified against git**; fetch before running. Candidate is exact O173/#509 `62792a7fc61b033b306b4445c337ed123946514d` with O169 Reader blob `1434c0b1485bfa59bd3dfe6f604ab555e35002a8`. No other owner branch is modified.

## Question and three competing choices

Does the shared 64 MiB/32768-entry decoded cache reduce **actual long-lived Reader process peak RSS** on a genuine revision-24 archive of >64 MiB distinct RAW S_BLOB members, and what is the full cost of evictions on a second sequential pass? Control A is source-exact historical unbounded cache. Control B is bounded O169. Control C (hypothetical remove cache entirely) bounds retention but incurs compulsory repeated decoding. This experiment compares A/B only; no product promotion or compression gain is implied.

## Prediction and disproof before measurement

Generate one fixed-seed, input-identical, non-Builder revision-24 archive containing **96 unique 1 MiB RAW blobs**, 96 one-blob logical regular files, and a valid dual index + footer; record source-independent per-file SHA-256 and the complete archive SHA-256. Reader must validate `verify()==96` before metrics if cheap enough and must return exact file lengths and SHA-256 for every read in both rounds. Preserve same source archive and same Python package codec/native helpers across arms; import *historical and candidate Reader source independently by exact Git blob*, in separate fresh child processes. Execute order A-B-B-A to limit monotone ambient drift. Cache is deliberately cold for the first pass; the second forward scan is adversarial to LRU.

Predicted retained decoded payload after both passes: A = 96 MiB, B = 64 MiB. If eviction behaves as plain LRU, B may miss all 96 on the second pass while A hits all. The **direction and size** of RSS and CPU/wall deltas are deliberately unpredicted; peak process RSS includes mmap/caller/native/in-flight, not only retained cache. If a source mismatch, any wrong bytes, a cache budget overrun, invalid full archive, missing observed process RSS, or missing unmodified historical control occurs, mark result INVALID/NO PRODUCT CREDIT, not green.

## Source isolation, economics, and boundaries

The synthetic generator uses public canonical `HDR/BHDR/FTR` + MsgPack + package Zstd index compression and intentionally bypasses Builder to avoid creation cost and representation-selector confounds. Index/footer must be verifiably authenticated. All test input bytes are shared, including exact metadata and settings; decoder differences arise only from actual Reader. Child output reports source SHA, sample count, cache payload/entry counts, incremental ru_maxrss, per-pass wall/CPU, strong content fold and any failure. Capture process startup separately. This is a **selective-read research court** on one high-entropy RAW regime, not the official r24/ZIP create/extract parity gate and not a realistic distribution of every file type. Report losses even if B beats A on RSS. No release thresholds, historical fixtures, comparator, CI topology or source identity contract may be changed.

## Concurrency / ownership

O169 #506 owns the cache. O173 #509 owns cache × prospective source custody and already measures a *scaled mocked VZIP scan-thrash mechanism*. O175 independently tests a **higher evidence rung** (genuine physical archive + actual installed package Reader RSS/CPU) without duplicating the mock or editing their branches. Keep one primary question; no discovery STATE.json mutation until decision-changing evidence is reconciled. Strong self-critique: small synthetic random RAW corpus may overstate cold-cache slowdown, Linux maximum RSS is cumulative and varies by host, and source-native codec must be identical across arms. No claim of general memory safety or universal performance.

**Decision:** retain cap for further productization only if exactness and genuine memory improvement survive the measured tradeoff; quantify any second-pass loss as explicit debt. If lower-rung court already predicts no useful benefit, stop before broader expensive benchmark; if a useful tradeoff survives, run heterogeneous authenticated VZIP and official full parity next. 

## Source-identification correction (append-only, 2026-10-26 UTC)

The earlier source SHA placeholder omitted the `5ac` segment; live Git `git rev-parse 4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b:src/cmpct/reader.py` confirms historical Reader blob **`e716233403dabd0966863c45635e18fa5ac6afb8`**. The original pre-result hypothesis and falsification thresholds above remain unchanged. Initial O175 Actions `40308133624` FAILED during source custody before installing/running the instrument due the mistaken expectation; this failure is preserved. The workflow expectation has been corrected without weakening the identity check.

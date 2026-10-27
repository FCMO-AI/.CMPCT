# J24V02 — source-exact sparse verification ABBA, preregistration

Date: 2026-10-27 UTC. Status: **PREDICTION ONLY; NO NEW MEASUREMENT**.
Parent/source owner: J24V01 draft #613 at exact `3b2bf3c2e033fa27d77b2355821dc0087aa46873`; candidate Reader Git blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710` (verify live before use).
Historical comparator: published `main@80c358f8824ec1b20d349c92ed94c898090969b0` / reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. CMPCT v0.30.0, on-disk revision 24. This branch is **science-only** and does not own Reader implementation, release law, format or Discovery STATE.

## Decision question
On **identical Builder-produced physical sparse archives**, does #613 reduce genuinely observed fresh-process peak own RSS of `CMPCT.verify()` by at least 128 MiB for a 256 MiB sparse file, without changing exact successful verification and without a confirmed economically material CPU/wall penalty? This is a held-out product-economics rung beyond J24V01's original one-arm 128-MiB ceiling, but not a full release benchmark or novel implementation.

## Strong controls and competing alternatives
- Unmodified released Reader is the strongest historical control; compare actual source bytes, not reconstructed algorithm or assistant-imagined baseline.
- Candidate source is unchanged J24V01; source SHA locked and native codec/import/effective index remain installed package semantics.
- Build the exact same 64 MiB and 256 MiB hole-dominant sources once (a different deterministic extent recipe from J24V01); require the authenticated `K_FILE/S_SPARSE` owner and exact logical SHA. Reuse each identical archive byte stream for **both** arms; do not rebuild per arm.
- Execute three independent ABBA rounds per size, each round order A, B, B, A for a total 12 fresh worker processes per geometry; process startup/import outside per-`verify()` CPU/wall, but count all own process RSS. Capture raw samples and source SHA for every child.
- Read own `/proc/self/status VmHWM` within the worker, **not** `RUSAGE_CHILDREN.ru_maxrss` (O224 demonstrated inherited-child contamination). Baseline and candidate each run on Ubuntu 24.04 / CPython 3.11, with fresh workers and identical native modules, exact source file paths and SHA.
- Independently reconstruct all paired medians, input hashes, source identity, count and vetoes from raw JSON, with deliberately corrupt receipt tests.

## Predictions, vetoes and kill/narrow
Primary hypothesis: on 256 MiB high-hole file, baseline-minus-candidate median own peak RSS >= 128 MiB and candidate median < 128 MiB; all 12 `verify()` outputs for that size equal the authenticated 1-file count and logical sha. On 64 MiB, positive memory direction is expected but **not required** to meet a fabricated threshold.
CPU/wall veto: candidate must not be >= 1.15x baseline **AND** >= +0.20 seconds absolute at 256 MiB for either CPU or wall medians. If this fires, retain RSS gain but mark as product regression debt, not promotion. Report ratios/absolute penalties regardless of the veto; don't erase smaller losses. Exactness/source/receipt inconsistencies disqualify the court.
Alternative explanation: startup, packages, process memory peak inheritance, physical sparse mode unavailable, filesystem caching or gzip/zstd codec changes create an apparent RSS delta. Reject/mark invalid unless source and archive identical, Builder genuinely emits S_SPARSE on both independent holes, and per-process source paths are proven. A true same-runner A/B may still have thermal/caching noise; preserve all raw data. Archive size, creation and extraction are **unchanged by a Reader-only patch**, not measured as a new claim; temp I/O, logical SHA hashing, source CPU and RSS must be disclosed.

## Scope / coordination / stronger adversarial check
No hardlink aliases, sparse extraction, Windows/macOS, 4 GiB ZIP64, arbitrary pathological extent counts or full Reader composition (#569) receive credit. Inherited J24V01 frozen r24 positive/hostile tests are not modified. Compare a zero-hole ordinary direct file only as a potential follow-up if RSS claim survives; ordinary Reader code is unchanged by J24V01.
Do not soften the negative if baseline and candidate run on different archive bytes, if RSS signal disappears, or if a smaller file contradicts generality. The independent evidence owner can replicate without replacing the #613 product owner. No `STATE.json` write: #574 currently owns stale-state reconciliation. No version, `SURFACE_REVISION`, format, freeze, benchmark or CI comparator change.

**Promotion law:** a J24V02 PASS credits one independent Linux verification-economics result, not packaged portability, product merge, official numerical performance, general security or release. Falsifiers, failures and raw receipts survive as evidence. No input-family-specific shipping admission is proposed.

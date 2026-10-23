# v0.31 — exact RAW-range × Reader/Public Proof composition preregistration (Phased2, 2026-10-23)

**Status:** PRE-RESULT, integration experiment, not product/release authority. **Base:** PR #271 `ec49f4ca4cd057c99e7417987620a8e44619862c` (Reader blob `ba6bb558bcb3b64acaf4ff47a1b78bcea28fb522`). **Independent capability owner:** PR #274 `5f357afced4a4945316af8b5bc1154b1950dc376` (Reader blob `3efcedca285298f4e085a6e06f19b73b6efbaa3c`). Published v0.30.0/r24 is unchanged.

## Distinct question
Can the *exact owner implementation* of opt-in bounded whole-SHA RAW selective reads (#274) coexist with the three-owner Reader safety fixes, prospective CI identity, strict Public Proof, and corrected 20-language localization already jointly present in #271 — without modifying old `read_range()`, codecs, Builder, artifact grammar, frozen tests or release thresholds?

## Baseline and strongest control
#274: 17 focused hosted tests green, but full Tests/Public Proof red on old v0.31 development, and substantive r24/ZIP performance blocked by inherited four-red preflight. #271: exact-head full Tests, Public Proof and Curated Localization green; source #268 (parent) passed substantive ABBA with zero confirmed regressions. **These are separate and inherited receipts, not proof for this composition.** Simpler control = leave two PRs independent; insufficient because their Reader changes and source identity cannot both be released without an integrated gate. Do not duplicate #270's sparse SHA/NAME_MAX owner or #272's fd-anchored root experiments.

## Implementation / expected result
Start from exact #271 HEAD. Transplant #274's method text **byte-for-byte** into the Reader at the same member-method boundary; prove the remaining Reader bytes are exactly #271's own source and the inserted method is exactly #274's own method. Copy #274's focused tests and economical benchmark script by Git blob identity; retain both original owner branches. Carry #274's hardening caveat without overwriting #271 safety updates. No new format, on-disk fields, native ABI, default API semantics, or release identity. Use existing full Tests, Public Proof, localization and r24/ZIP gates on exact final head.

**Prediction:** general Tests and focused RAW tests pass, Public Proof/localization remain green, deterministic archive sizes match, and no confirmed wall-time regression appears because the change adds only an otherwise-uninvoked method. A same-runner regression must be preserved and investigated, not waived.

**Kill/narrow:** any changed pre-existing Reader byte, owner-method mismatch, default-range behavior drift, failed negative controls, public/localization failure, deterministic size increase, authentic ABBA threshold failure, or portability regression blocks promotion. A skipped/failed preflight benchmark cannot establish performance success. CRC+SHA against rewritable archive metadata is consistency only, not authenticity or time-of-check snapshot isolation. Opt-in full verification spends O(raw blob size) per invocation; 64MiB default cap is a source-size admission bound, not CPU-free access.

## Ownership/concurrency/evidence
Independent composition claim; do **not** move, merge, rewrite, or close PR #271, #274 or any discovery state. Branch based on immutable SHA (not changing a neighbor's current head); recheck refs before final shared state. Durable results are exact-head workflow runs, test artifacts, Git blob fingerprints and this preregistration. Source-neutral A/B to PR #271 must use identical inputs and freeze real engine/configuration. Tests and local simulations are not shipping evidence. Only update `docs/discovery/STATE.json` if a decision-changing primary frontier change occurs and coordination ownership permits it.

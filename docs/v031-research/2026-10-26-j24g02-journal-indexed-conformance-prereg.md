# J24G02 preregistration — independent journal vectors against shared indexed Reader

Status: **FROZEN BEFORE TEST IMPORT / RESULT**. UTC date: 2026-10-26.
Authority: `AGENTS.md`, `docs/FORMAT.md`, `docs/HARDENING.md`, `docs/discovery/DISCOVERY_ENGINE.md`; no release-law mutation.

## Scientific question and baseline
PR #358 (O7) replaces a separate ordinary-Reader delta transaction interpreter with the strict indexed `cmpct.validation._apply_delta`. It reports genuine journal tests and large targeted open-time savings, but its ordinary Reader's signed-journal semantics have not been evaluated against the independently generated fixed J24G01 revision-24 archive bytes. J24G01 PR #481 already recorded seven passing new tests against a different Reader source. Shared Writer-derived fixtures could conceal correlated Reader/Writer bugs.

Target inherited head: PR #358 `2c5334392c57f9c0f685c3751712acf0e242efae`.
Independent control: PR #481 `fe8dc99de2c47c42c4a7ad95f83bb3bf3c36aa81`; frozen test blob `63024d52c0d7a97d63adaabf13f9a0cff6499de8`; frozen JSON blob `74a39263954a84debd7ce6992cfa71fc1ed4dd91`.

## Falsifiable hypotheses
H1 — The genuine ordinary indexed Reader on PR #358 recognizes the independent checkpoint and SHA-committed delta, with the exact last valid generation's paths, content hashes, selective byte ranges and delta depth.
H2 — A physically complete but unauthenticated later footer, a truncated append and a corrupted authenticated delta digest must never override the last valid ancestor. Corrupt physical content must fail verification despite authenticated index bytes.
H3 — Composing these two provenance-independent mechanisms requires **zero edits** to original Reader, validation, Writer, format, test assertions or frozen JSON, and neither imports a new dependency nor changes archive bytes. If that fails, preserve the red and diagnose, not weaken oracle.

## Controls, alternatives, and kill condition
Strong simple control: J24G01 on historical released Reader in PR #481; exact source/fixture blobs from Git. Different alternative: regenerate journal with current Writer, rejected as lower-grade common-mode evidence. Broad synthetic random suites already belong to O7 and do not replace this fixed-byte test. Kill or narrow this compatibility claim on *any* existing unchanged J24G01 assertion failure or inability to bind exact Git HEAD/source. A generic suite red from unrelated inherited release identity is separately classified, not hidden as green. The cheapest decision is copying unchanged two committed files and executing existing PR-head pytest; do not buy new full performance matrix for a conformance decision.

## Costs, risks, and allowed mutation
A small regression test file and a 3.6-KiB JSON fixed fixture, plus this document and eventual source-bound result. Test runtime and source carrying cost are the main exported costs. Reader/Writer/format/ABI and release locks must remain byte-identical to PR #358. Branch isolation; PR stacked on PR #358; no merge/release. Independent CI must report the exact tested SHA and observed results; pending is not success.

## Decision-complete handoff
If all seven cases pass on the true test-bearing head, leave this as evidence-enablement for owner #358 / #481, **not** measured product speedup. If red, preserve which operation and source broke. Check the generic test verdict independently; do not grant promotion until all normative gates pass.

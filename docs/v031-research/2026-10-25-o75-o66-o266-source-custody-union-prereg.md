# O75 — Prospectively compose O66 full Builder custody with v0.31 candidate fingerprint

**Date:** 2026-10-25 (UTC). **Status:** preregistered before source overlay. **Evidence class:** release/evidence infrastructure and product composition, not compressor invention.

## Frozen owner sources and question

- O66 owner PR #422 exact base `d485ce2d0fe3b1543173f1d3be0aaec01b324564`, which carries O63 one-buffer VZIP transactional fallback, O47 Win32 physical hardlink fidelity, O48 unsupported-entry refusal, and O59 exact historical parent custody. At its exact head the installed O66 5-host court is green, while generic tests still report **four inherited historical-v0.30 fingerprint/surface reds**.
- O266 owner PR #266 exact source `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1` (8 changed paths) separately passes generic CMPCT tests and establishes **prospective v0.31** fingerprint without rewriting published v0.30 lock.
- Both branches share immutable canonical v0.31 ancestor `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Current O66 changes do not touch O266's eight paths.
- **Question:** Can the eight O266 files be transplanted as exact original Git blobs on the unchanged O66 Builder/product source, causing the four unrelated inherited generic reds to disappear **while O66's installed cross-platform court and historic comparison remain valid**?

## Prediction and decision boundaries

Predict all eight O266 file blobs remain byte-identical to their source; O66 original Builder, Codec, original tests, frozen input/source fixtures and published `docs/V030_RELEASE_LOCK.json` remain byte-identical; the generic full test suite passes with no four inherited reds; O66 installed five-host court passes with justified Windows POSIX skips; prospective candidate fingerprint checks required source additions, omissions/renames, unsafe symlink, and public README/surface package consistency.

**Falsify composition** if an original-owner source blob drifts, historical v0.30 release-lock blob changes, any original O66 product/fixture blob changes, any of the inherited negative tests remain failing, a new failure appears, or O66 exact-source court rejects the combined product. Do not weaken existing assertions, tests, workflow thresholds, release comparator, corpus, format, or source graph. A fast-suite PASS is not release permission.

**Unresolved stronger gates:** effective official r24/ZIP performance job must RUN (not just admin green or skipped), exact candidate source fingerprint must match evaluated HEAD, general portability and safety remain to be reconciled by actual CI. No compression-size/speed gain may be claimed for the identity transplant. Do not merge/release as part of this experiment.

## PARETOBONK alternatives / controls

1. Merge/overwrite canonical v0.31: rejected; neighboring agents and product owners are concurrent.
2. Edit immutable `docs/V030_RELEASE_LOCK.json` to satisfy old tests: rejected; falsifies published identity.
3. Exclude four tests or relax assertions: rejected; fake-green.
4. Reimplement O266 from prose: rejected; source drift/maintenance duplication.
5. **Chosen:** exact Git-blob transplant of the eight O266 paths onto a new O66 child. Strong controls: original O66 five-host court, O266 independently green generic suite, source SHA equality, untouched product files, and authentic generic tests.

## Expected cost and counterfactual

Eight small source/CI artifacts; no new decode semantics or archive bytes. Counterfactual: importing the already verified O266 candidate identity *before* running O66 generic CI would likely have avoided repeated attribution of known inherited four reds. This is a hypothesis until hosted test confirms the composition. Avoid creating a second project-state database; this prereg, PR and Actions evidence are linked, not an independent canonical frontier.

## Ownership

Independent integration only, no mutation of #422/#266/#418/#405 or any canonical branch, no Discovery STATE rewrite. Reconcile newly landed owner heads before late edits.
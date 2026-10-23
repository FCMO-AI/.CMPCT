# CMPCT v0.31 — Explicit VZIP late-fallback candidate contamination (preregistered)

**Issue:** #206. **Owner:** independent Phased1 VZIP fallback repair. **Start authority:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`; codec blob `29526db4203723d83523fc95d074c346b63d7587`. **Scope:** explicit `.zip/.whl` fallback only, without changing format revision 24, hidden ZIP selection, S_PACK threshold, Deflate strategy, or release gates.

## Pre-result hypothesis

`make_vzip_recipe` calls the live `Builder.add_content` before all members are proven virtualizable. If a first STORED member is admitted and a later legal raw DEFLATE member uses `Z_FIXED` strategy and cannot be reproduced by any default-strategy `deflate_level_for` level, the recipe returns `None` after leaving dead member candidates in `Builder.cands`. `Builder.build` encodes every candidate, so fallback archives may contain dead physical blobs without violating content reconstruction.

## Simplest control, alternative, falsifier

Control: treat the *same input ZIP* opaquely from the outset, using the ordinary `S_BLOB` fallback; compare complete archive bytes, candidate reachability, source SHA and exact reconstruction in reproducible single-worker mode. Positive control: an all-virtualizable ZIP must produce exactly the inherited successful VZIP candidate state and stream output. Alias control: if the abandoned first member's content already exists outside the ZIP, its hints and Deflate observation counts must not change. Exception control: a callback that raises late must not retain earlier speculative mutations, while preserving prior exception behavior.

Prediction: prior Builder scan on late failure has extra candidates and potentially larger final bytes. If the current untouched source already rolls back speculative entries or the reproduced stream is actually accepted by `deflate_level_for`, **falsify** the mechanism and do not patch. If the candidate fixes state but changes successful ZIP bytes or increases memory unboundedly versus baseline, **do not promote**.

## Proposed narrow repair

Use a reversible, per-hash candidate mutation journal around the existing successful `make_vzip_recipe` callback (not a duplicate ZIP parser and not an additional Deflate pass). On `None` or error, restore previously-existing candidate hints and Deflate multiplicities, and remove only candidates created during the abandoned probe. On success, preserve byte-for-byte the original callback and candidate order. This differs from storing every inflated member in a staging array and avoids retaining a second unbounded copy of entire ZIP logical contents.

## Evidence plan

1. Construct an authentic deterministic two-member ZIP through the standard library: accepted STORED member followed by valid `Z_FIXED` DEFLATE unmatched by all inherited levels; independently decode via `zipfile`.
2. Run unmodified source to capture the baseline failure in focused installed-package tests; subsequently run the same tests on the fix with no criterion weakening.
3. Test existing-candidate alias, failure on raised exception, successful ZIP control, eight-explicit archive cohort, full opaque-reference byte parity, SHA/reconstruction, and adversarial second-member ordering.
4. Run exact-head hosted tests, full Tests and applicable r24 parity; treat failures and unrun comparisons honestly. Quantify extra memory/CPU if evidence requires; no release claim from a focused green.
5. Keep claim narrow: this removes **abandoned candidate emissions**, not malicious ZIP parsing, concurrent source mutation, or all other archive creation performance bottlenecks.

No product or release credit from this preregistration.

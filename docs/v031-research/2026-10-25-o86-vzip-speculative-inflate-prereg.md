# O86 preregistration — bounded speculative VZIP inflate admission

**Date:** 2026-10-25 UTC. **Status:** prospectively registered, outcome unknown. **Base:** O63 PR #418 exact `18e32cae012f5dca9fc47f10d194f8b81005c85c`, format r24, released v0.30.0 unchanged, v0.31 research only.

## Real question and baseline

Original `make_vzip_recipe()` calls `ZipFile.read(zi)` into a complete Python bytes allocation, then performs up to ten full Deflate recompressions, for each candidate. It reads arbitrarily large *declared* ZIP members before deciding if the virtual recipe wins complete stored bytes. Previous O68 #424 establishes some highly inflated ZIPs lose bytes and huge CPU versus opaque, but O71 #427 proves inflation ratio **alone** cannot reject VZIP safely as a global economic discriminator.

Is a finite **absolute speculative decode budget**, charged before inflation from cumulative `ZipInfo.file_size` across members, a technically valid fail-safe way to bound the optional VZIP probe while retaining exact ordinary fallback and all sub-budget virtual wins? This is **resource admission**, not a compression predictor; it must not be marketed as a universal reduction in bytes or an exact memory cap on all Builder operations.

## Prediction, controls and kill conditions

A high-ratio single ZIP with >64 MiB declared uncompressed bytes but <1 MiB physical ZIP size is expected to be rejected by the speculative VZIP probe immediately, and the unchanged Builder should store and reconstruct the original ZIP opaque, without an unbounded `ZipFile.read()` attempt. Stronger control: invoke the unchanged O63 policy with a permissive 256 MiB probe budget on that identical ZIP and measure the original CPU/memory/complete archive bytes, rather than comparing against a different corpus. This control may be slower but smaller; preserve that downside. Secondary control: legitimate structurally favorable VZIP ZIPs with combined members <64 MiB must yield the **same complete archive bytes and exact member reconstruction** as the original O63 policy on same corpus (except environment metadata; use `reproducible=True`). Malformed ZIP, non-Deflate, and failure to reproduce exact members always preserve opaque fallback; a resource guard must not accept a broken recipe.

Proposed budget **64 MiB total declared inflated member bytes per ZIP** (whole speculative parser, not each-member separately), configurable via an explicit positive integer environment policy for research; use `None` default for direct standalone codec callers to avoid silently changing its API behavior. Rejection returns existing `None` VZIP fallback, not an exception or unrepresentable archive. Check budget **before any member inflation or speculative mutation**, to make rejection cheap. The Builder's own ZIP physical-byte capture remains outside this speculative bound and must be measured/acknowledged.

Disproof: selected heavy input is not VZIP, budget fails to bypass `z.read`, sub-budget archive SHA changes, fallback cannot reconstruct exactly, explicit budget introduces unexpected errors, or shipping admissible test suite breaks. If a strong inherited candidate saves large bytes only above the absolute budget, record regression debt and consider a user-controlled selective override; never loosen the release parity gate.

## Evidence ladder / economics

1. Code-level inspect O63 actual `make_vzip_recipe` and Builder `_transactional_vzip_recipe`; confirm no prior equivalent guard.
2. Small deterministic Python/ZipFile archive establishes declared/captured sizes, with identical-input strict control.
3. Implement minimal codec preflight + Builder policy on isolated draft branch, add focused authentic Builder/Reader tests for under/over budget, and hostile malformed budget.
4. GitHub Actions installed-host court with source-identity logging, raw measurements and no fake benchmark pass; compare complete stored bytes, create CPU/wall, correct extraction and input/outputs hashes. Held-out other ZIP structural family is needed before promotion.
5. Any official parity/reference output change remains **release debt**, not covered by this science.

## Ownership / concurrency

PR #418 owns VZIP transactional fallback; #424, #427, #430 and #443 own related economic/integrity science. O86 is an independent, narrow bounded-resource candidate, not a replacement or surprise merge of these PRs. Work in new branch based on exact #418. Do not modify owner branches, benchmarks, release gates or format. Current `STATE.json` has an independent reconciliation owner #440; do not write it.

## Counterfactual

Compare against explicit opaque fallback and existing high-inflation negatives; a **ratio-only** gate is already falsified by O71. If absolute memory budget is practical, preserve lesson as resource admission distinct from economic admission; do not generalize beyond measured data.

**Outcome at preregistration:** pending measurement.

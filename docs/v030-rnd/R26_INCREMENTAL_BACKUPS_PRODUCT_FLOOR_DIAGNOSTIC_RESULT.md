# R26 — Incremental Backups Product-Floor Diagnostic Result

Status: **INVALIDATED BEFORE RESULT-BEARING ARM EXECUTION; SUPERSEDED BY R27**

Frozen preregistration: `docs/v030-rnd/R26_INCREMENTAL_BACKUPS_PRODUCT_FLOOR_DIAGNOSTIC_PREREG.md`.
Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

## What happened

The first registered R26 workflow execution (`33825838543`) stopped in its substrate preflight because the allowlist omitted one control-plane-only workflow-registration file. No corpus arm executed and no scientific result was produced. The workflow guard was repaired without changing the frozen corpus, arms, locality ceiling, measurement grammar, or interpretation law.

The next execution (`33826416770`, job `100879923022`) passed the Git substrate guard and compiled the frozen instrument, but the instrument then stopped before corpus generation or any of the three arms because its frozen full-release fingerprint equality was impossible to satisfy:

- frozen expected release fingerprint: `aa5693f6d5899e61753bf005b70f3460f82f477535d941807d14e35788e7c1ee`
- observed release fingerprint after registering R26: `dfdf8cc31caa44ebba260eabc3477dc50bc1554b1b785937cc9aee4bdfaba1bb`

No R26 JSON evidence artifact exists because execution terminated before the result document could lawfully be constructed.

## Causal diagnosis

This was not product-code drift and is not scientific evidence about Incremental Backups.

`docs/V030_RELEASE_LOCK.json` intentionally includes both `benchmarks/v030_*.py` and `.github/workflows/v030-*.yml` in the canonical release fingerprint. R26 itself introduced `benchmarks/v030_r26_incremental_backups_floor_diagnostic.py` and `.github/workflows/v030-r26-incremental-backups-floor-diagnostic.yml`. Therefore freezing the pre-R26 *full release fingerprint* and then requiring that same fingerprint from a repository containing the R26 instrument made the equality self-invalidating.

The release fingerprint is behaving correctly: changing a release-critical evidence harness must invalidate old release receipts. The design error was using that evolving release fingerprint as the immutable identity of an unchanged **product substrate** inside a newly added diagnostic.

## Preserved negative constraint

Do not freeze a full v0.30 release fingerprint and then add a `benchmarks/v030_*.py` or `.github/workflows/v030-*.yml` instrument that is itself inside the fingerprint surface while requiring equality to the pre-instrument fingerprint. A diagnostic that must prove product-code immutability across its own registration should bind the product substrate independently (for example, exact authority head plus fail-closed diff allowlist) and record the current release fingerprint as evidence rather than pretending it remains unchanged.

Reopening predicate: none for R26 itself. The scientific question remains unanswered and is transferred unchanged to a superseding freeze with corrected substrate binding.

## Decision

**INVALID_MEASUREMENT_BINDING / NO SCIENTIFIC RESULT.**

R26 grants no product, performance, locality, or release credit and provides no evidence for D1–D5 about Incremental Backups. R27 supersedes only the impossible substrate-binding mechanism; the three arms, corpus, selected-member locality observation, <=8x hard ceiling, outputs, and interpretation law remain unchanged.

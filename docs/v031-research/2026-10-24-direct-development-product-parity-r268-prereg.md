# O1 prereg — direct-development r24 product parity for the v0.31 Writer × salvage × evidence union

Date: 2026-10-24 (UTC)
Status: **PREDICTION REGISTERED BEFORE NEW COURT IMPLEMENTATION/RESULT**
Episode: `v031-r268-direct-development-parity-o1`
Repository: `FCMO-AI/.CMPCT`
Starting candidate source: `fb87f582918bd7ca0f16559eed2f782739977048` (PR #328)
Direct canonical development base: `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` (`agent/v031-development` at orientation)
Research-only branch: `agent/phased3-v031-direct-development-parity-r268-20261024`
Evidence tier: hosted, same-runner, complete-corpus **r24 core parity**; **not** a release milestone or external domination claim.

## Primary question

The existing PR #323/#328 official performance receipts are **A/A** (same Builder/Reader/native source on both arms) because they compare against immediate stacked parents. They verify the admission/comparator machinery, **not** whether the cumulative Writer, Reader-integrity and bounded-salvage candidate preserves actual canonical v0.31 create/extract economics.

Can the real PR #328 candidate pass the **unchanged official r24 corpus/comparator** when compared against the *canonical development source*, on one runner with base-native materialization and all historical release semantics maintained?

## Alternatives and BONK

- Merely rerun the parent A/A: cheap but does not answer the product question (reject).
- Blindly merge four owners: incorrectly treats A/A as promotion (reject).
- Handwritten 1-file timing microbenchmark: cheaper but cannot answer corpus-wide release-parity economics (reject for this promotion-relevant decision).
- Duplicate or relax comparator: forbidden.
- **Selected:** an isolated single-use exact-source workflow that reuses the canonical parity harness, same corpus construction, native base materializer, 2×7 medians/arm in ABBA, mandatory correctness preflight, official numeric checker and unchanged 0-B / conjunctive 5%-and-3-ms thresholds. It changes no Builder, Reader, Writer, tests, existing workflow, historical record, shared Discovery state or release policy.

## Prospective hypothesis / kill boundary

Hypothesis: Writer lease/salvage safety and source-custody corrections do not materially worsen the accepted non-hostile r24 create/extract workload; 16/16 deterministic archive sizes remain <= direct development and no repeated timing row crosses both existing thresholds. This is a **prediction, not a result**.

**Kill / narrow:** One +1B archive-size regression, a valid repeated timing regression exceeding both threshold conditions, any correctness preflight red, mismatched source/core SHA, missing corpus manifest/source identity, base-native build failure, nonfinite metric, cross-platform or semantic failure means **NO product promotion**. Infrastructure failure is not an observed product loss. Any size shrink is only a direct-base local benefit, not external ZIP/Zstd domination.

Stronger control: PR #328 same-code official A/A 16/16 equal-size and no timing reds. Plausible alternative: cumulative native/Reader/Writer changes cause real overhead or different archive bytes masked by source-identical stacked-parent A/A. A green workflow with a SKIPPED substantive performance job would **not** decide this question.

## Required court design / measured surfaces

- Checkout actual head SHA, verify it matches GitHub event and store source identity.
- Verify direct-base commit is ancestor, materialize that **actual** historical source and its native engine through existing pinned helper. Never substitute the candidate for the base.
- Candidate harness and one shared, normalized, SHA-fingerprinted corpus; no independently generated input trees.
- Run real library and CLI create/extract, two symmetric ABBA invocations per arm, `CMPCT_PARITY_REPS=7`, preserve raw repeated source records.
- Run the **unmodified** official `tools/check_performance_regression.py` on the aggregated outputs, using the exact currently normative flags.
- Preserve control/candidate SHA, full artifacts, console verdict, and job conclusion. Separate benchmark direct-base parity from production release authority.
- Treat CPU/RSS/temporary I/O, adverse mutation behavior, Windows/macOS compatibility, full union with PR #326 and external competitors as **unmeasured unless separately observed**.

## Concurrency, authority, and future decision

Stack only on PR #328; do not write to any source-owned implementation or branch. PR #311 Writer/salvage, PR #306 comparator, PR #320 classifier, PR #326 native/Reader remain independent owners. `docs/discovery/STATE.json` is a staleable cache and must not be overwritten. The experiment uses its own source-identity and artifacts. If the court is green, maintain draft and ask owners to reconcile complete source and safety/platform gates before any release. If red, localize the actual failing dimension rather than weakening inherited acceptance.

## Prediction/outcome separation

This file intentionally contains no new measured results. Append a distinct outcome file or PR comment after the hosted court resolves; never rewrite the prediction to match the observations.

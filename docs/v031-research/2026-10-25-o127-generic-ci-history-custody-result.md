# O127 — Generic CI historical-source custody, observed result

Status: **EVIDENCE-ENABLEMENT SUCCESS FOR THE SEVEN HISTORICAL-SOURCE FAILURES. GENERAL CI STILL FORMALLY RED. NO PRODUCT CREDIT.**

Date: 2026-10-25 UTC. PR #473 stacked on O99 PR #455, original base `2fbdba24d0dfb29231c3710eb9b272a2aea89b9b`. GitHub Actions source/results `da0bab078ff0a9da6bd9d603adc1da6b88834cb2`, [run 40240633437](https://github.com/FCMO-AI/.CMPCT/actions/runs/40240633437), job `121311452051`. Scientific question/predictions frozen *before* code in `2026-10-25-o127-generic-ci-history-custody-prereg.md`.

## Frozen A/B

**A — genuine baseline:** O99 PR #455, run [40217166617](https://github.com/FCMO-AI/.CMPCT/actions/runs/40217166617), job `121240942402`, exact head `2fbdba24...`. Original `actions/checkout@v4` exact-head but default fetch-depth=1. Pytest: **838 passed, 7 skipped, 11 failed**. Seven failures were `git show` / `git rev-parse` unable to load historical source `src/cmpct/builder.py` at `29d9688a` (3), `4545d7d5` (3), `7efcc511` (1). Four independent inherited v0.30 release/fingerprint/surface expectations also failed.

**B — single-mechanism candidate:** O127 source head `da0bab078ff0a9da6bd9d603adc1da6b88834cb2`, same underlying product/source/test tree except research preregistration and `.github/workflows/tests.yml` history-custody policy. `actions/checkout@v4`, same exact head, `fetch-depth: 0`, plus `git rev-parse --is-shallow-repository` false assertion before unmodified `python -m pytest -q`. Pytest: **845 passed, 7 skipped, 4 failed in 369.69 s**. All seven former historical-source failures now pass. Remaining four failures are the same inherited fingerprint/surface assertions, specifically:
- `tests/test_performance_base_native_release_custody.py::test_historical_native_materializer_is_release_fingerprinted`;
- `tests/test_public_attribution.py::test_surface_revision_records_attribution_campaign`;
- `tests/test_v030_ci_topology_split_receipts.py::test_authoritative_v2_classifier_is_release_fingerprint_driven`;
- `tests/test_v030_release_fingerprint_surface.py::test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs`.

**Independent Git ancestry:** `compare_commits` verified `29d9688a`, `4545d7d5`, `7efcc511` are direct ancestors of the base `2fbdba24` by 75/80/24 commits respectively; merge-base equals each historical source commit. No historical implementation was recreated, waived, rebaselined, reinterpreted, or substituted.

## Prediction versus result

P1 non-shallow checkout: **PASS**, confirmed directly in exact-head job step.

P2 all three original immutable Builder Git objects available: **PASS by genuine unchanged historical comparison tests**, 7 former Git-object failures become passes. Three-way source fingerprints/hashes remain enforced by those tests.

P3 only history-dependent failures cured, unrelated release/surface remain: **PASS**. Four unrelated tests remain red; the candidate is **not** a green general suite or product release candidate. The eight other pre-existing categories were not altered.

P4 historical objects unreachable: **NOT TRIGGERED**; all ancestors reachable under full advertised history. Alternative per-SHA fetching is unnecessary unless future evidence shows cost substantially higher or full history inadequate.

P5 checkout economics: logged action group start/end from baseline `2026-10-25T17:36:03.7522594Z` to next binding step `17:36:04.9394160Z`, approximately **1.187 s**; candidate `2026-10-25T22:32:03.0406404Z` to next binding step `22:32:05.1795948Z`, approximately **2.139 s**, observed increase **~0.952 s** on distinct hosted runner activations. These are **single uncontrolled cross-run checkout timings**, not paired A/B CPU/RSS/bandwidth measurements and cannot justify a robust scaling claim. The candidate full suite ran 369.69s; history custody adds ~1s at this observed scale and does not mask test failures.

## Reviewer self-critique / safety

This does **not** fix four independent source-fingerprint/surface assertions. Those remain red. PR #266 owns prospective v0.31 identity and modifies the same workflow in a disjoint region, so integrated authorship must reconcile both before promoting. PR #473 is a **DRAFT** explicitly stacked on O99 #455 for faithful reproduction. No automatic merge, no version bump, no changed release lock or assertion. A general branch needing a historical source not ancestor/advertised ref may still need a different mechanism. Complete history increases network resources and adds incidental Git object exposure *only within the already authorized public repository*.

No product archive size, create/extract throughput, RSS, native ABI, parser semantics, recovery, format, platform/read boundaries or release evidence is measured by O127. Artifact gain is **CI evidence integrity**, not compression.

## Counterfactual and prospective transfer

A cheap check, `git rev-parse --is-shallow-repository`, at the start of historical-source test lanes would have explained the seven failures before work on Builder internals. Prospective transferable discriminator: **if a test demands immutable historical blobs, require authenticated full history or exact fetch before running it; never repair apparent product regressions by reducing history controls**. No repeated multi-project evidence exists to self-modify normative discovery policy. No `docs/discovery/STATE.json` change: its current owner is PR #440.

## CI and handoff

Evidence-producing exact-head source: `da0bab078ff0a9da6bd9d603adc1da6b88834cb2`. Run 40240633437 generic test: **FAILURE**, but the fixed seven history-dependent cases are PASS and other four unchanged FAIL. PR body version originally failed Engineering Evidence on a missing named heading (run 40240633491), subsequently corrected **without changing validator requirements**, and rerun 40241312067: **SUCCESS** on original result-bearing head. CI Topology, Version Discipline, R36 Attribution: **SUCCESS** on the original result-bearing head. Official ZIP performance: **NOT RUN / NO CREDIT** for this CI-only PR.

Next executable: coordinate with #266 to land both `fetch-depth: 0` and prospective identity step on the same source branch; run the complete unchanged pytest against that composition, requiring 849 passing (845 already seen + four independently owned legacy assertions), preserving release/evaluator authority. This is a target, **not** a measured result. If result-document commit produces a newer SHA, that SHA requires its own exact-head CI and no automatic inheritance of earlier green checks.

No merge. No release credit. No product changes.
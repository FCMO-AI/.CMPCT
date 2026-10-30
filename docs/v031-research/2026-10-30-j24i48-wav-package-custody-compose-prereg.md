# J24I48 — Preregistered prospective package-custody composition (2026-10-30 UTC)

**Status:** prospective, not product proof / not release authority. Parent native-WAV streaming candidate is PR #788 at exact `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`; proven independent CI fix is PR #352 at `93e9a00fd352ac567e9b069654aa145148370d42`. This document is committed **before** porting CI files or fingerprint metadata. No native implementation, format, benchmark comparator, threshold, historical release lock or version may be modified.

## Baseline and causal finding

PR #788's exact-source installed package workflow run [40982724661](https://github.com/FCMO-AI/.CMPCT/actions/runs/40982724661) had three installed-wheel jobs and fifteen CPython 3.10–3.14 cross-platform compatibility jobs SUCCESS, but final `desktop-package-evidence` FAILURE, job `123827349733`. The aggregator calls the published v0.30 historical release-lock strict CLI against a **prospective v0.31/unreleased candidate**. PR #352 independently addresses this specific CI epoch/custody mismatch with a v0.31 prospective source fingerprint, exact HEAD equality, three artifact SHA-bound names, the unchanged eighteen feeder jobs, and strict smoke/ABI/dependency assertions. PR #788 does **not** contain `tools/check_v031_candidate_fingerprint.py` or `docs/V031_CANDIDATE_FINGERPRINT.json`. A Git tree inspection confirmed all 31 other manifest-required paths exist in #788's base.

This is a **D0 evidence/custody repair**, not codec optimization. The previous #788 native-stream A/B result and its general-test four-red status are inherited; this composition does not erase either.

## Primary question, controls, kill condition

Will the **exact existing** #352 prospective package workflow + source fingerprint logic and required manifest, transplanted into an isolated branch of #788, make the final three-platform installed package aggregator issue an authentic successful `cmpct-v031-desktop-package-evidence-v1` receipt tied to the new candidate HEAD, while preserving all eighteen installed-wheel/CPython feeder jobs and source mismatch rejection?

Controls: (1) leave the prior historical v0.30 release lock immutable; (2) reuse #352 code and tests rather than inventing a competing fingerprint algorithm; (3) never remove smoke/ABI/CPython/dependency checks; (4) inspect CI topology; (5) preserve all red tests, including unrelated native symlink source-identity and General Tests fingerprint gates; (6) do not mistake skip/cancel/pending for substantive proof.

**Prediction:** a source-bearing exact-head run generates three OS artifacts with expected SHA and a successful aggregator; a non-source latest-commit may correctly classify out but provides no product receipt. **Kill / narrow:** missing mandatory candidate paths, mismatch of source SHA, ignored corrupted/foreign artifact, any installed-wheel failure, stale/head-mismatched receipt or unexpected topology rejection forbids package-gate credit. Do not claim full release, general-test or native-core acceptance solely from this gate.

## Measured versus planned

Inherited: #788 Ubuntu/macOS/Windows native streaming product court passed and component 8/32-MiB performance was measured; #352 package aggregate had independently succeeded on its own different source. **Not yet measured:** composed #788+#352 exact-head package acceptance or installed streaming candidate parity. **Not in scope:** native parser edits, selective-range semantic relaxation, freeze/release or benchmark regeneration.

## Ownership and continuity

#352 owns the original repair; #788 owns native streaming. This child is an **explicit integration/composition court**, not a forked competing implementation. Final merges require conflict/head revalidation by maintainers. Reader native and Python test failures remain independent debt. Discovery STATE is a staleable cache and is not a lock.
# ONE-G0.2 plan-carried current-root hash — terminal result

**Status:** REJECTED as the ordinary integrated-current-root direction in this tested per-segment form.

## Authority

- Branch: `research/cmpct1`
- Exact result-bearing source: `80a84c338cc83313ccfdaee382bd0265601f81e8`
- Workflow run: `34082669659`
- Job: `101620804169`
- Artifact: `10004180884`
- Artifact digest: `sha256:62c3380cea5b400e719ceb8efd96a155e70b9fd51785cdcc3f7ddfff97ba6022`
- Preregistration: `docs/one/prereg/ONE_G02_PLAN_CARRIED_CURRENT_ROOT_HASH_PREREG_2026-09-06.md`

The workflow's ONE tests, strict C build, frozen benchmark, aggregate publication and artifact preservation all completed successfully. The workflow is red only because the final preregistered decision-enforcement step correctly rejects the measured result.

## Hypothesis

A validated ONE Law+Surprise segment plan defines the current logical byte stream exactly. Incremental SHA-256 over Ref source ranges and Surprise target ranges could therefore, in principle, produce exactly the current-root digest while eliminating a later whole-target root-hash pass.

The falsifier compared native OpenSSL EVP SHA-256 over the complete target against native incremental EVP updates over the already-built ONE segment sequence. Segment construction was excluded from both timing arms: this was a marginal-cost feasibility gate before any full-writer integration.

## Semantic result

PASS.

- candidate digest == whole-target native SHA-256 == Python `hashlib.sha256(target)`;
- native productive segment plans remained equal to the independent Python oracle;
- ONE semantic/hostile tests passed;
- strict `-Wall -Wextra -Werror` native build passed.

The negative is therefore economic, not semantic.

## Frozen aggregate result

| metric | measured | preregistered gate | outcome |
|---|---:|---:|---|
| mature productive median candidate / whole-target SHA | **1.056231x** | <=1.05x | FAIL, narrow |
| mature productive worst row | **1.328964x** | <=1.15x | FAIL, hard |
| fragmented mature median | **1.311556x** | <=1.10x | FAIL, hard |
| control mature median | **1.014234x** | <=1.08x | PASS |

Decision emitted by the benchmark: `reject_plan_carried_current_root_hash`.

## Causal interpretation

The control result is useful: a one-Surprise logical stream is only ~1.4% slower than one whole-target SHA-256, so the SHA implementation/context itself is not the dominant problem.

The failure grows with segmentation. Repeated `EVP_DigestUpdate` calls plus per-segment branching, bounds/control work and switching between source/target ranges erase the possible value of deleting the later contiguous target-hash pass. Fragmented productive plans are the decisive witness: **1.311556x** median, with a **1.328964x** worst mature productive row.

This is consistent with ONE's accumulated speed evidence: replacing a cheap regular contiguous memory pass with irregular fine-grained control can lose even when it appears to eliminate work at the architectural level.

## Terminal decision / reopening predicate

Do **not** integrate arbitrary per-segment root hashing into the shared/native writer, and do not rescue it with a `segment_count` threshold, relation classifier or corpus-specific dispatch.

The underlying pass-elimination question is not fully dead. It may be reopened only through a causally different design in which SHA state is advanced at coarse, regular boundaries already present in the observation/segmentation traversal, so update count is independent of Law fragmentation. Such a design must compare `segment plan + separate whole-target SHA` against a single combined observation/segment/hash traversal and preserve an identical Segment plan and digest.

This receipt grants no full-ingest, full-writer, authenticated-placement, RSS, selective-access, durability, arbitrary-discovery, v0.29/v0.30 or release authority.

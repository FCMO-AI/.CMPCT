# R32 — Regenerable-Deflate Output-Dead Ordinary-Zstd Elision Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: `docs/v030-rnd/R31_REGENERABLE_DEFLATE_CODEC_EFFORT_REHABILITATION_RESULT.md`.

Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

## Causal basis

R31 preserved the R30 byte/locality gain but disproved single-level sufficiency. On both frozen targets:

- `single-zstd12` and `single-zstd9` produced the **same complete archive bytes and SHA-256 as full-search**;
- both specialized exactly 180 regenerable exact-Deflate-backed candidates / 980,226 raw bytes;
- reducing Zstd effort recovered wall time monotonically, with level 9 faster than level 12;
- neither one-level arm restored the same-runner `release-all-exact` floor.

Because materially different ordinary Zstd outputs at levels 12 and 9 did not change even one final archive byte, the cheapest remaining causal hypothesis is that the ordinary Zstd audition is output-dead for this frozen semantic class and can be omitted entirely. R32 is that falsifier.

This is **not** a level sweep and does not reopen the 64KiB retention family.

## Forge classification

- parent state: breakthrough rehabilitation;
- diagnosis: **D3 speculative candidate audition / S5 plateau**;
- intervention: **R2 concept compression** — remove an audition whose outputs are causally unselected;
- parent terminal constraint: single-level sufficiency retired.

## Frozen semantic admission

All byte-winning arms preserve R30 `locality-risk-v1` retention exactly:

`retain := exact_stream_bytes >= 65_536 OR raw_bytes > 8 * exact_stream_bytes`.

The R32 specialization is admitted only when all are true:

- the raw candidate carries nonempty exact-Deflate provenance (`candidate.deflates`);
- it is not canonical-retained;
- it is not a retained secondary exact stream;
- raw length is `<65_536 B`, matching the inherited small-candidate ordinary-Zstd branch.

No workload name, path, extension-only rule, corpus identity, benchmark label or observed output size may enter admission.

## Frozen arms

1. `release-all-exact`
   - retain every canonical exact Deflate stream;
   - inherited encoding for everything else;
   - same-runner timing/RSS/byte floor.

2. `full-search`
   - R30 locality-risk retention;
   - inherited `_encode_candidate` unchanged, including ordinary Zstd `(12,9,5)` for admitted small candidates;
   - exact byte-winning control.

3. `no-ordinary-zstd`
   - R30 locality-risk retention unchanged;
   - for the frozen R32 semantic admission only, preserve inherited RAW fallback, WAV/FLAC/Deflate candidates when applicable, and Zstd-dictionary candidate when inherited conditions permit;
   - construct **no ordinary `CODEC_ZSTD` candidate** for that admitted class;
   - every candidate outside the admitted class uses inherited `_encode_candidate` unchanged.

## Frozen targets and execution

Use exactly the repaired deterministic R30/R31 pair:

- full `neutral_hostile_v1/06_incremental_backups`;
- exact isolated `snapshot_2.zip` projection from the generated tree.

For every arm/target:

- 3 fresh Python worker processes;
- complete archive bytes and SHA-256;
- median build wall time;
- median peak RSS;
- strong product verification and exact product-tree identity;
- operation-derived virtual-member decoded-context amplification;
- exact-Deflate retained/regenerated counts/bytes;
- specialized candidate count/raw bytes for `no-ordinary-zstd`.

Generator tree and nested-member SHA-256 must match before interpretation.

Result authority must record `evidence_head` from `CMPCT_EVIDENCE_HEAD`; `GITHUB_SHA` is diagnostic only.

## Hard invariants

- exact reconstruction / strong verification;
- R30 retention/locality grammar unchanged;
- every measured virtual-member amplification `<=8x`;
- preferred-arm complete bytes **and archive SHA-256** equal `full-search` on both targets for promotion;
- preferred-arm RSS within 10% of same-runner `release-all-exact`;
- specialized path executes on >0 candidates;
- no product edit or release credit from this diagnostic;
- frozen corpus/comparator/thresholds/grammar immutable after first result-bearing execution.

## Runtime law

Use the existing performance-gate materiality law unchanged: a slowdown is material only if both `>5%` relative and `>3 ms` absolute.

Rehabilitation succeeds only if `no-ordinary-zstd` is **not materially slower than same-runner `release-all-exact` on either target**.

## Frozen terminal grammar

`PROMOTE_NO_ZSTD_TO_GLOBAL_REHAB_BUILDER`

iff all are true:

- `no-ordinary-zstd` bytes and SHA-256 equal `full-search` on both targets;
- strong verification/tree identity pass everywhere;
- locality `<=8x` everywhere;
- RSS within 10% of same-runner release on both targets;
- no material runtime regression versus same-runner release on either target;
- specialized path executes on both targets.

`OUTPUT_DEAD_CONFIRMED_RUNTIME_DEBT_REMAINS`

iff exact byte identity / verification / locality / RSS all survive but runtime remains materially slower than release on either target.

`OUTPUT_DEAD_INFERENCE_FALSIFIED`

iff `no-ordinary-zstd` changes complete archive bytes or SHA-256 relative to `full-search` on either target while substrate/correctness remain valid.

`SUBSTRATE_OR_CORRECTNESS_FAILURE`

for identity, verification, malformed-result, missing-locality or execution-boundary failure.

## Success handoff

`PROMOTE_NO_ZSTD_TO_GLOBAL_REHAB_BUILDER` authorizes only a superseding protected-workload/global carrying-cost Builder. That Builder must test the generic semantic predicate across all implicated protected workloads, preserve exact product bytes where required, account runtime/RSS/locality, and expose any native/platform or maintenance carrying cost before productization.

No R32 outcome directly changes canonical product policy.

## Failure / next-cause law

If output-dead identity is confirmed but runtime debt remains, ordinary Zstd audition is retired as a sufficient owner and the residual runtime must be phase-attributed before another intervention. Do not remove additional codecs by intuition.

If exact archive identity changes, the R31 archive-level inference is falsified and the next action is to record which candidate interaction caused the divergence; do not rescue the result by weakening byte identity.

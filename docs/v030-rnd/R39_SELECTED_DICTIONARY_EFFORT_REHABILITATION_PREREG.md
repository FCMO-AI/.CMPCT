# R39 — Selected-Dictionary Effort Rehabilitation Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: `docs/v030-rnd/R38_REGENERABLE_DEFLATE_ENCODE_CRITICAL_PATH_RESULT.md`.

Authority evidence head for parent result: `eee03e4db0cba73cf46bb018f2c106c28a04a7c0`.

## Observed debt

R38 retired the single-straggler explanation for the residual R30/R32 byte-win runtime debt. On the repaired Incremental Backups pair, 180 structurally identical small text candidates with one exact-Deflate alternative account for 97.33% of summed positive encode-task excess on Full Backups and 99.94% on isolated `snapshot_2.zip`. Under the byte-winning arm those candidates no longer retain their exact Deflate streams and all 180 select dictionary-Zstd (`CODEC_ZSTDDICT`) as the physical content representation.

R38 therefore establishes that the remaining cost is real selected-representation work, not output-dead ordinary-Zstd audition and not executor collection order. The lowest-sufficient next intervention is to reduce dictionary encode effort for exactly that evidenced semantic family, while pricing any byte erosion explicitly.

## Forge classification

- parent state: breakthrough rehabilitation;
- diagnosis: **D2/D3 selected-codec effort debt after speculative-work retirement**;
- minimum intervention: **R2**, one adjacent codec-effort step;
- saturation signal: **S5** if the selected dictionary family cannot recover the release runtime floor without surrendering the protected byte win;
- R38 terminal handoff: `RETIRE_SINGLE_OWNER_SEARCH; CLUSTER_SELECTED_DICTIONARY_FAMILY`.

This is not a level sweep. R39 tests one causally adjacent effort reduction only.

## Frozen operational family

A candidate enters the R39 specialized path iff all of the following are true at encode time:

1. it has nonempty exact-Deflate provenance (`candidate.deflates`);
2. its hash is **not** present in `canonical_deflate` after the inherited R30/R32 retention decision;
3. its raw length is `<65_536 B`;
4. its content hints contain `text` (the normalized extension hint used by the repaired generator family); and
5. a dictionary is available and inherited dictionary competition would ordinarily be applicable.

No workload name, member path, filename, corpus identity, benchmark label, output-size oracle, candidate hash allowlist or post-hoc winner identity may admit a candidate. R38's observed selected `CODEC_ZSTDDICT` winner is evidence for choosing this family; it is not itself an oracle used for dispatch.

The frozen repaired target pair must exercise exactly **180** specialized candidates / **980,226 raw bytes** in the byte-winning arms. Any mismatch is substrate failure, not a result to reinterpret.

## Frozen arms

1. `release-all-exact`
   - retain every canonical exact Deflate stream exactly as inherited by the frozen R38 release control;
   - inherited encode policy unchanged;
   - same-runner byte/runtime/RSS floor.

2. `dict12-control`
   - use the frozen R32 `no-ordinary-zstd` byte-winning arm unchanged;
   - dictionary compression remains inherited level **12**;
   - this is the same-runner protected byte-win control.

3. `family-dict9`
   - identical to `dict12-control` except for the frozen R39 operational family only;
   - preserve inherited RAW, retained-Deflate, secondary-stream, WAV/FLAC and all other applicable candidates;
   - preserve ordinary-Zstd elision already established by R32 for the inherited regenerable-Deflate semantic class;
   - replace dictionary compression level **12** with exactly level **9** for the specialized family;
   - every non-family candidate uses the inherited byte-winning `_encode_candidate` unchanged.

No level 5 arm is permitted in this freeze. If level 9 fails, a lower effort level requires a new superseding freeze justified by this result rather than an in-run sweep.

## Frozen targets and execution

Use the exact repaired deterministic R38 target pair:

- full `neutral_hostile_v1/06_incremental_backups`;
- isolated exact `snapshot_2.zip` projection from that generated tree.

For each arm/target:

- **5** fresh Python worker processes;
- complete archive bytes and SHA-256;
- uninstrumented `Builder.build` wall time;
- peak RSS;
- strong product verification + exact product-tree hash;
- operation-derived virtual-member decoded-context amplification;
- retained/regenerated exact-Deflate counts/bytes;
- specialized R39 candidate count and raw-byte total.

Five repetitions are frozen to reduce timing noise without turning the experiment into a large search. Promotion uses same-runner medians only. R38 per-task timings are diagnosis provenance and may not serve as R39 runtime credit.

The result schema must record explicit `evidence_head` from `CMPCT_EVIDENCE_HEAD`; `GITHUB_SHA` is diagnostic only and must not be used as checkout authority.

## Hard invariants

- exact reconstruction and strong verification everywhere;
- inherited R30/R32 exact-Deflate retention grammar unchanged;
- inherited R32 ordinary-Zstd elision grammar unchanged;
- locality `<=8x` for every measured virtual member;
- no >10% peak-RSS regression versus same-runner `release-all-exact` for any promotable arm;
- `dict12-control` must remain strictly smaller than `release-all-exact` on both targets;
- specialized family must be exactly 180 candidates / 980,226 raw bytes on both byte-winning arms;
- no archive grammar, reader, worker-count, corpus, retention threshold, competitor setting, release threshold or platform invariant may change;
- no product edit or release credit from this experiment.

## Runtime materiality law

Use the inherited R30 law unchanged: a regression is material only when **both** `>5%` relative and `>3 ms` absolute versus the same-runner `release-all-exact` median.

R39 asks whether the single level-9 dictionary effort reduction can make the byte-winning family non-materially slower than release on **both** protected targets.

## Byte accounting law

Any `family-dict9` byte erosion relative to `dict12-control` must be reported exactly in bytes and as a fraction of the inherited R38/R32 saving. Aggregate runtime improvement may not hide lost compression.

A family-level rehabilitation win requires `family-dict9` to remain **strictly smaller than same-runner `release-all-exact` on both targets**. Exact byte identity with `dict12-control` is not required because this experiment deliberately changes a selected representation. Such a result remains Builder evidence only and requires Hostile Reviewer/global carrying-cost work before productization.

## Frozen terminal grammar

`PROMOTE_DICT9_TO_HOSTILE_REVIEWER`

iff all are true:

- all arms strongly verify with exact tree identity;
- all locality measurements are `<=8x`;
- `dict12-control` is strictly smaller than release on both targets;
- `family-dict9` is strictly smaller than release on both targets;
- `family-dict9` has zero material runtime regressions versus same-runner release across both targets;
- `family-dict9` peak RSS is within 10% of release on both targets;
- both byte-winning arms exercise exactly 180 specialized candidates / 980,226 raw bytes.

This promotes only to a Hostile Reviewer/global-carrying-cost phase. It does not authorize a product policy change.

`DICT9_BYTE_WIN_RUNTIME_DEBT_REMAINS`

iff the result is valid, `family-dict9` stays strictly smaller than release on both targets, but remains materially slower on at least one target.

`DICT9_RUNTIME_RECOVERED_BYTE_WIN_LOST`

iff the result is valid, `family-dict9` has zero material runtime regressions on both targets, but is not strictly smaller than release on at least one target.

`DICT9_BOTH_DEBTS`

iff the result is valid and `family-dict9` both loses the strict byte win on at least one target and remains materially slower on at least one target.

`SUBSTRATE_OR_CORRECTNESS_FAILURE`

for target identity, verification, specialized-family identity, locality, malformed result, inherited-control byte-win or execution-boundary failure.

## Success handoff

A `PROMOTE_DICT9_TO_HOSTILE_REVIEWER` result requires a new frozen Hostile Reviewer covering at minimum:

- exact byte erosion versus `dict12-control` and percentage of the protected R38/R32 saving retained;
- protected-workload/global nomination carrying cost without workload dispatch;
- all relevant runtime/RSS/locality rows;
- native/platform implementation burden if the encoder policy crosses those boundaries;
- whether the family rule conceptually subsumes or merely adds policy complexity.

Only that review may recommend productization.

## Falsification / retirement

If level 9 remains materially slower while retaining the byte win, the claim that one adjacent dictionary-effort reduction is sufficient is falsified. Do not silently sweep levels. A lower effort rung is allowed only under a new freeze that cites R39's measured remaining gap and prices the expected byte erosion.

If level 9 closes runtime only by losing the strict byte win, preserve that Pareto point as negative evidence and do not weaken the product floor.

## Strongest expected self-critique

R38's family is unusually coherent and large inside the repaired Incremental Backups corpus, but Addressable Opportunity Mass outside that regime is not yet established. Even a protected-target rehabilitation does not prove that a global family rule earns its nomination, maintenance, fuzz/native/platform and portfolio carrying costs. R39 is deliberately only a bounded Forge Builder, not a general-purpose breakthrough claim.

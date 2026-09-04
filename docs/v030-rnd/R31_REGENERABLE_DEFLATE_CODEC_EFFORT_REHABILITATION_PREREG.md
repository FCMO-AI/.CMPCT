# R31 — Regenerable-Deflate Codec-Effort Rehabilitation Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: `docs/v030-rnd/R30_DEFLATE_LOCALITY_RISK_CONDITIONAL_BUILDER_RESULT.md`.

Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

## Observed debt

R30 recovered the entire mature 64KiB Deflate-retention byte opportunity on repaired Incremental Backups while preserving strong verification, 1.0x operation-derived locality and flat measured RSS:

- full-backups: `8,088,199 -> 8,055,779 B` (`-32,420 B`), but `0.469236 -> 0.563493 s` (`+20.09%`, `+94.256 ms`);
- nested-only: `2,231,158 -> 2,197,416 B` (`-33,742 B`), but `0.305421 -> 0.421710 s` (`+38.07%`, `+116.289 ms`).

The simple mature-64k arm and the content-derived locality-risk-v1 arm made the same retention decision: retain 12 canonical streams / 1,918,264 B and regenerate 180 streams / 283,585 B. Their complete bytes were identical and their median runtimes differed by only ~1–2 ms. The conditional predicate is therefore not a credible owner of the ~0.1 s debt.

In inherited `Builder._encode_candidate`, a retained canonical Deflate stream exits immediately, whereas a regenerable small Deflate-backed raw candidate re-enters ordinary codec competition. For raw candidates below 64 KiB that means Zstd levels `(12, 9, 5)` are all constructed before the smallest physical representation is selected, plus any independently applicable dictionary candidate. R31 asks whether this speculative three-level audition is the dominant exported cost and whether it can be collapsed without giving the R30 bytes back.

## Forge classification

- parent state: breakthrough rehabilitation;
- diagnosis: **D2 execution architecture / D3 speculative candidate audition**;
- minimum intervention: **R2/R3**;
- saturation signal: **S5** if redundant Zstd auditions dominate the rehabilitated path;
- terminal parent decision: `REHABILITATE_DEBT`.

This is not a threshold sweep. The 64KiB retention family is not reopened. R31 preserves R30's locality-risk retention rule exactly and changes only encoding effort for candidates that R30 already classified as safely regenerable.

## Frozen worldview

For a candidate carrying exact nested-Deflate provenance that is *not* retained as a physical exact stream under R30's rule, the ordinary `<64KiB` Zstd `(12,9,5)` tournament is likely unnecessary work. On this regime, level 12 is expected to be the winning ordinary Zstd candidate often enough that constructing levels 9 and 5 mostly spends CPU to rediscover losers.

The strongest simple control is therefore **single-Zstd-12 audition** for this already-regenerable semantic class, while retaining every independently applicable non-Zstd candidate required by inherited semantics. A second arm, **single-Zstd-9**, tests whether a lower-effort/lower-level encoding can retain the byte opportunity even when exact byte identity is lost.

## Frozen arms

All arms use R30 `locality-risk-v1` exact-stream retention unchanged:

`retain := stream_bytes >= 65_536 OR raw_bytes > 8 * exact_stream_bytes`.

1. `full-search`
   - inherited ordinary `_encode_candidate` after R30 retention;
   - for small ordinary candidates, Zstd `(12,9,5)` remains fully auditioned.

2. `single-zstd12`
   - only for a candidate with nonempty exact-Deflate provenance (`candidate.deflates`) that is not canonical-retained and not a retained secondary stream;
   - preserve inherited RAW fallback;
   - preserve WAV/FLAC/Deflate competition if applicable;
   - preserve Zstd-dictionary competition when inherited conditions permit it;
   - replace ordinary Zstd `(12,9,5)` with exactly level `12`;
   - every other candidate uses inherited `_encode_candidate` unchanged.

3. `single-zstd9`
   - same semantic boundary as `single-zstd12`, but ordinary Zstd audition is exactly level `9`;
   - this is a falsifier/effort tradeoff arm, not the preferred promotion arm.

No workload name, path, extension-only dispatch, corpus identity, benchmark label or output-size oracle may choose an arm or special case. Admission is the already-existing exact-Deflate provenance plus R30's frozen content-derived retention decision.

## Frozen targets and execution

Use the exact repaired deterministic R30 target pair:

- full `neutral_hostile_v1/06_incremental_backups`;
- isolated exact `snapshot_2.zip` projection from that generated tree.

For each arm/target:

- 3 fresh Python worker processes;
- complete archive bytes and SHA-256;
- build wall time;
- peak RSS;
- strong product verification + exact product-tree hash;
- operation-derived virtual-member decoded-context amplification;
- retained/regenerated exact-Deflate counts/bytes;
- count and raw-byte total of the semantic candidates that entered the specialized R31 codec path.

The repaired generator tree and isolated nested-member SHA-256 must match before any performance interpretation.

The result schema must record an explicit `evidence_head` from `CMPCT_EVIDENCE_HEAD`; `GITHUB_SHA` is diagnostic only and must not be used as checkout authority.

## Hard invariants

- exact reconstruction and strong verification;
- R30 locality-risk retention grammar unchanged;
- locality `<=8x` for every measured virtual member;
- no >10% peak-RSS regression versus `full-search`;
- no byte regression versus R30 `full-search` for preferred-arm promotion;
- no product edit or release credit from this experiment;
- frozen target/corpus/comparator/thresholds may not be edited after first result-bearing execution.

## Runtime materiality law

Use the existing R30 law unchanged: regression is material only when both `>5%` relative and `>3 ms` absolute.

For rehabilitation success, the preferred arm must do more than avoid a regression against `full-search`: it must close enough of R30's exported debt that, against the R30 release-all-exact runtime floor, neither frozen target is materially slower under that same law.

Because R31's control itself is R30's byte-winning `full-search`, the instrument must carry the frozen R30 release-all-exact medians as reference constants solely for the rehabilitation decision:

- full-backups `0.4692364889999965 s`;
- nested-only `0.3054214809999962 s`.

These constants are not re-estimated or widened after execution. A future product/global Builder must remeasure direct arms on one runner before promotion.

## Frozen terminal grammar

`PROMOTE_SINGLE12_TO_GLOBAL_REHAB_BUILDER`

iff all are true:

- `single-zstd12` complete archive bytes and archive SHA-256 equal `full-search` on both targets;
- strong verification/tree identity pass everywhere;
- locality remains `<=8x` everywhere;
- RSS is within 10% of `full-search` on both targets;
- `single-zstd12` is not materially slower than the frozen R30 release-all-exact runtime floor on either target;
- the specialized path actually executes on >0 candidates.

`BYTE_IDENTITY_WIN_RUNTIME_DEBT_REMAINS`

iff exact bytes/verification/locality/RSS are preserved but the preferred arm remains materially slower than the frozen R30 release runtime on either target.

`PARTIAL_BYTE_RETENTION_RUNTIME_WIN`

iff `single-zstd12` loses exact R30 byte identity but remains strictly smaller than the R30 release-all-exact complete bytes on both targets and closes the runtime debt on both. This is evidence only; it does **not** authorize promotion because R30's full byte gain was not retained.

`SINGLE9_ONLY_TRADEOFF`

iff the preferred arm fails byte/runtime rehabilitation but `single-zstd9` demonstrates a strictly smaller-than-release, runtime-rehabilitated tradeoff on both targets.

`NO_REHABILITATION`

for a valid result that satisfies none of the above.

`SUBSTRATE_OR_CORRECTNESS_FAILURE`

for identity, verification, missing-locality, malformed-result or execution-boundary failure.

## Success handoff

A `PROMOTE_SINGLE12_TO_GLOBAL_REHAB_BUILDER` result authorizes only the superseding protected-workload/global carrying-cost Builder required by R30, now using the single-level effort rule as part of the candidate. It does not authorize direct product policy changes.

That superseding Builder must still cover all relevant protected workloads, exact byte/runtime/RSS/locality accounting, no workload dispatch, native/platform carrying cost where implicated, and the inherited release floors.

## Falsification / retirement

If `single-zstd12` cannot preserve R30 bytes, or preserves them but leaves material runtime debt, the claim that redundant lower Zstd-level auditions are sufficient to rehabilitate R30 is falsified. Do not respond by sweeping arbitrary Zstd levels. Use the result to attribute the remaining cost and either:

- isolate another measured owner in the ordinary codec path;
- move to a structurally different execution strategy;
- or preserve R30 as a scoped byte/locality opportunity that is not yet productizable.

The next step must be caused by measured residual cost, not by threshold folklore.

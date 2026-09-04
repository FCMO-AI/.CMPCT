# R41 — Global Dictionary-Effort Concept Compression Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent hostile-review evidence: `docs/v030-rnd/R40_SELECTED_DICTIONARY_EFFORT_HOSTILE_REVIEW_RESULT.md`.

## Why this is not another scalar sweep

R40 rejected the exact R39 `family-dict9` rule as a product policy because its protected local gain transferred to only **1/15** accepted public workloads and **0.3685%** raw Addressable Opportunity Mass while requiring one new permanent encoder branch.

The repository nevertheless contains a pre-existing writer-policy inconsistency:

- initial/archive `Builder._encode_candidate()` compresses dictionary-eligible text candidates at Zstd-dictionary **level 12**;
- transactional `_encode_update_blob()` compresses dictionary-eligible text updates at Zstd-dictionary **level 9**.

R41 does **not** ask whether level 8, 10, 11, a smaller file threshold, a different extension list, or a new backup-specific predicate is better. It asks whether one already-used writer effort can replace two inconsistent writer efforts and thereby make the R39 behavior a consequence of a simpler canonical rule.

Worldview under test:

> **A single dictionary effort of 9 may be sufficient for canonical writer behavior because the transaction path already uses it; if full-build level 9 preserves the accepted byte floor while reducing runtime, it removes rather than adds policy entropy.**

Hostile alternative:

> The transaction path's level 9 is only an update-speed compromise. Applying it to full builds erodes too many deterministic bytes, loses strict wins, or produces no meaningful runtime benefit. In that case the R39 local benefit cannot be rescued by global policy unification and R40's scoped product rejection stands.

## Forge classification

- diagnosis: **D2/D5** — duplicated writer effort policy plus a proven local rehabilitation whose exported cost is portfolio entropy;
- intervention: **R1/R2** concept compression — unify an existing encoder effort choice; no representation or information-model change;
- saturation law: R40 forbids further subset/threshold sweeps without new causal evidence;
- RPS: **86/100** — high falsifiability, zero reader-grammar ambition, direct carrying-cost attack, full-matrix decision surface.

## Immutable source identity

Use the exact accepted repair-v6 15-workload public matrix consumed by `benchmarks/mosaic_v029_generalization_bench.py` and R40:

- accepted repaired v0.29 aggregate identity: **137,499,525 B**;
- inherited v0.30 absolute saving hurdle: **687,783 B**, unchanged;
- accepted per-workload tree hashes and baseline bytes unchanged;
- no corpus, generator, metadata normalization, competitor, locality, runtime, RSS or release threshold may change after result-bearing execution begins.

R41 remains Forge diagnostic evidence only. It cannot rewrite the August 17 historical record or grant release credit.

## Frozen mechanism

Preserve the R40 selected representation/retention substrate exactly.

The only candidate intervention is:

> for every candidate for which the existing writer would evaluate `CODEC_ZSTDDICT` with the already-trained archive dictionary, evaluate that dictionary codec at **level 9 instead of level 12**.

No new family predicate is allowed. No workload/path/name/hash/extension subset beyond the writer's already-existing dictionary eligibility is allowed. No dictionary-training change is allowed. No new codec, grammar, parser, framing, recovery, locality, Deflate-retention, micro-pack or reader behavior is allowed.

The experiment must account for the fact that `src/cmpct/transactions.py::_encode_update_blob()` already uses dictionary level 9. This pre-existing duplicate policy is the causal reason R41 is admissible after R40; it is not retroactive evidence that global level 9 is safe.

## Frozen arms

For each accepted workload:

1. `release-all-exact` — unchanged R40 release control;
2. `dict12-control` — unchanged R40 selected-representation control with dictionary level 12;
3. `global-dict9` — byte-for-byte identical mechanism to `dict12-control` except every already-eligible dictionary compression uses level 9.

All three arms consume the same generated source tree per workload.

## Frozen execution protocol

For all 15 workloads:

- prove accepted tree identity before interpretation;
- run **5 fresh processes per arm per workload**;
- record deterministic complete archive bytes and SHA-256;
- strong-verify exact source reconstruction;
- record build wall time and peak RSS;
- record dictionary-eligible candidate count and raw bytes globally;
- record candidates whose selected complete representation/bytes differ between level 12 and level 9;
- preserve exact Deflate-retention accounting;
- derive operation-based selected-member locality wherever applicable and require `<=8x`;
- preserve all current resource/correctness bounds.

Unchanged material runtime rule:

`candidate - baseline > 3 ms` **and** `(candidate / baseline - 1) > 5%`.

RSS regression is material when median peak RSS exceeds the corresponding baseline by more than **10%**.

## Frozen accounting

Per workload publish:

- accepted/observed tree identity;
- three-arm complete bytes;
- candidate byte delta versus release and dict12;
- fraction of any positive dict12 saving retained;
- five fresh build-wall samples and medians;
- runtime materiality versus release and dict12;
- five peak-RSS samples and median/materiality;
- dictionary-eligible candidate count/raw bytes;
- number/raw bytes of candidates whose dictionary output differs between levels;
- strong verification/determinism;
- locality availability and maximum amplification.

Aggregate publish:

- number of workloads with any dictionary-eligible candidates;
- number of workloads whose complete archive bytes change at global level 9;
- aggregate dictionary-eligible raw bytes / aggregate logical bytes as an AOM proxy;
- aggregate byte erosion versus dict12;
- retained positive saving versus release;
- strict-win losses versus release;
- material runtime/RSS regressions versus release;
- runtime change versus dict12 only where the candidate actually changes dictionary work;
- exact permanent policy-state delta relative to today's two writer policies.

Aggregate gains may not hide a losing required row.

## Concept-compression carrying-cost law

R41 succeeds only if the proposed product shape **reduces or does not increase policy entropy**.

The intended product interpretation, if evidence supports it, is a shared writer-level dictionary-effort constant/helper used by both initial build and transactional update paths. That means:

- no new reader grammar states;
- no native reader/C-ABI changes;
- no platform parser copies;
- no workload-specific policy branch;
- no new file-size/extension/hash allowlist;
- no additional encoder decision branch beyond dictionary eligibility that already exists;
- removal/subsumption of the current full-build-vs-update `12`/`9` effort inconsistency.

If evidence requires retaining separate 12 and 9 policies plus adding an admission rule, this experiment has failed its concept-compression purpose even if one workload improves.

## Frozen protected gain

The public Incremental Backups row must remain a strict byte win versus `release-all-exact`, remain within locality/RSS bounds, and have no material create-time regression versus release.

R41 need not reproduce R39's exact 25,323-byte saving because global effort changes more candidates than the R39 family. It must preserve a material portion of the protected gain and must not turn the workload red.

## Frozen terminal decision grammar

Exactly one decision must be emitted.

### `PROMOTE_GLOBAL_DICT9_PRODUCT_PREREQUISITE`

Allowed only if:

- all 15 identities match and all outputs strongly verify deterministically;
- **zero** workloads lose a strict byte win versus release that dict12 held;
- **zero** global-dict9 activation workloads become a complete-byte loss versus release because of the intervention;
- protected Incremental Backups remains a strict byte win and has no material runtime/RSS/locality regression;
- zero material runtime regressions versus release across all 15;
- zero >10% RSS regressions versus release;
- all applicable locality remains `<=8x`;
- dictionary eligibility demonstrates opportunity beyond the single R40 backup workload;
- measured global runtime/effort evidence is directionally compatible with using level 9 as the one writer policy;
- permanent encoder policy state is zero or negative relative to the current separate full-build level-12 and transaction level-9 choices.

This authorizes only the next explicit product prerequisite. It does not authorize productization or release.

### `RETAIN_SPLIT_POLICY_R40_BOUNDARY`

Emit when global level 9 is correct and bounded but loses deterministic bytes or strict wins enough that one global writer effort is not product-worthy. Preserve R39 and R40; do not add the rejected special-case branch.

### `REHABILITATE_GLOBAL_DICT9`

Emit only when the broad policy shows meaningful cross-workload opportunity and preserves the protected gain, but a specific measured runtime/RSS/byte/carrying-cost debt has a lower-sufficient non-subset repair. A superseding freeze is required.

### `RETIRE_DICTIONARY_EFFORT_UNIFICATION`

Emit when global level 9 has no material product upside, broadly erodes bytes, or demonstrates that the existing transaction/full-build effort split reflects a real operational tradeoff rather than accidental duplication.

### `SUBSTRATE_OR_CORRECTNESS_FAILURE`

Emit for identity drift, nondeterminism, failed strong verification, locality >8x, malformed evidence or frozen-mechanism drift. No performance interpretation is allowed.

## Anti-sunk-cost / reopening law

If R41 rejects global level 9, do not respond with levels 8/10/11, size thresholds, extension subsets, backup allowlists or per-workload dispatch. Those are exactly the scalar/subset search that R40's negative evidence forbids without new causal evidence.

A later effort-policy experiment requires a new semantic owner or independent transfer evidence, not a closer number.

## Strongest preregistered self-critique

The fact that transactional updates already use level 9 is architectural evidence of duplicate policy, not proof that the two operations should share the same Pareto point. Full archive creation optimizes a complete immutable artifact; append updates may rationally value latency more heavily. R41 is deliberately capable of concluding that the split is justified.

A second risk is that a broad global-dict9 change may produce tiny deterministic byte erosion across many rows while saving little wall time because dictionary compression is not the dominant path. In that case concept compression is aesthetically attractive but economically wrong, and the correct outcome is to retain the split policy plus the R40 product boundary.

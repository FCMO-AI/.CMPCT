# R40 — Selected-Dictionary Effort Hostile Review Result

Status: **TERMINAL — `REHABILITATE_GLOBAL_CARRYING_COST`; VALID HOSTILE-REVIEW EVIDENCE; NO PRODUCT OR RELEASE CREDIT**

Frozen preregistration: `docs/v030-rnd/R40_SELECTED_DICTIONARY_EFFORT_HOSTILE_REVIEW_PREREG.md`.

Parent Builder evidence: `docs/v030-rnd/R39_SELECTED_DICTIONARY_EFFORT_REHABILITATION_RESULT.md`.

## Execution authority

- workflow run: `33864127192`
- result-bearing job: `100995031670`
- exact evidence head: `6f2c05eacb94476a1a676ca2f9cc2efecc4f5407`
- release fingerprint observed by the frozen instrument: `db0c82c143553698d1c48588104c8c7385125dee10398205ac0f628a688b5d97`
- immutable workflow artifact: `9933436522`
- artifact ZIP SHA-256: `73239cba57973f0d171f2037d420a9ee83facd69450633cd9e4df4d865a19386`
- frozen 15-workload / 3-arm / 5-fresh-process hostile review: **PASS**
- frozen completeness and terminal-decision guard: **PASS**
- workflow topology self-check: **PASS**

The evidence run was preserved under exact-SHA custody while later branch changes touched only CI routing. Those later commits do not inherit release credit from this diagnostic receipt.

## Terminal decision

The frozen instrument emitted:

> **`REHABILITATE_GLOBAL_CARRYING_COST`**

R39's local mechanism survives hostile review on its protected target, but it does **not** establish enough transferable opportunity to justify a new permanent general-purpose encoder branch in its present form.

This is a product-economics rejection of the present rule, not a refutation of the underlying local causal fact.

## Protected Incremental Backups result

The accepted public Incremental Backups row remained exact and healthy:

| Arm | Complete bytes | vs release | median create | vs release create | peak RSS | locality |
|---|---:|---:|---:|---:|---:|---:|
| `release-all-exact` | 8,088,591 | — | 0.482083 s | — | 475,068 KiB | 1.0x |
| `dict12-control` | 8,056,179 | **-32,412 B** | 0.519895 s | +7.84% / +37.812 ms, material | 475,068 KiB | 1.0x |
| `family-dict9` | 8,063,268 | **-25,323 B** | 0.486971 s | +1.01% / +4.888 ms, non-material | 475,068 KiB | 1.0x |

`family-dict9` therefore retained **25,323 / 32,412 B = 78.13%** of the level-12 byte saving while recovering about **6.33%** create time relative to `dict12-control`. It gave back **7,089 B** relative to level 12 but remained a strict byte win versus release. Strong verification passed and selected-member read amplification remained 1.0x.

This is directionally consistent with R39: lowering dictionary effort from 12 to 9 preserves most of the protected byte gain while eliminating the material create-time regression.

## Global hostile-review result

Across the complete accepted repair-v6 15-workload matrix:

- accepted repaired v0.29 aggregate identity: **137,499,525 B**;
- inherited v0.30 absolute saving hurdle: **687,783 B**, unchanged;
- logical input represented by the 15 rows: **265,969,714 B**;
- family activations: **1 / 15 workloads**;
- activation workload: `neutral_hostile_v1/06_incremental_backups` only;
- specialized candidates: **180**;
- specialized raw bytes: **980,226 B**;
- Addressable Opportunity Mass proxy: **0.00368548 = 0.368548%** of aggregate logical bytes;
- family-predicate examinations: **180**;
- specialized / examined nomination density: **1.0** inside the already-eligible family;
- workloads where dict9 changed complete bytes versus dict12: **1 / 15**;
- positive dict12 saving versus release: **32,412 B**;
- positive dict9 saving versus release: **25,323 B**;
- aggregate byte erosion versus dict12: **7,089 B**;
- lost dict12 strict-win workloads: **0**;
- false-positive admission workloads that lost versus release: **0**;
- material runtime regressions versus release: **0**;
- >10% RSS regressions versus release: **0**;
- applicable locality violations: **0**.

The global result is therefore unusually clean but also unusually narrow: no hidden correctness, byte-loss, runtime, RSS, locality, reader, native or platform disaster appeared; the mechanism simply failed to transfer beyond the one public backup workload.

## Carrying-cost accounting

The frozen carrying-cost model remained:

- new reader grammar states: **0**;
- new native reader / C-ABI states: **0**;
- new platform parser copies allowed: **0**;
- existing Zstd-dictionary metadata remains sufficient: **yes**;
- projected permanent Python encoder policy branches: **1**.

That last branch is the decisive debt. A one-branch policy is small in absolute code terms, but the hostile-review contract asks whether a permanent general-purpose exception is justified by addressable value rather than whether it is easy to type. With activation on only one of fifteen accepted workloads and only **0.3685%** raw AOM, R40 cannot call the current rule low-cost enough to promote.

## Scoped negative constraint

Preserve the following constraint for future Forge work:

> **On the accepted repair-v6 15-workload public matrix and the frozen R38/R39 exact-Deflate-backed small-text predicate, dictionary effort 9 is a valid local rehabilitation for Incremental Backups but does not demonstrate transferable product opportunity: it activates on only 1/15 workloads and 0.3685% of aggregate logical bytes. A new permanent encoder branch for this exact predicate is therefore not product-justified under R40.**

This constraint is scoped to:

- the exact R38/R39 predicate;
- effort 9 versus effort 12;
- the accepted repair-v6 15-workload matrix;
- the frozen R40 representation/retention/locality/runtime/RSS semantics;
- evidence head `6f2c05e...` and release fingerprint `db0c82c...`.

It is **not** a universal claim that dictionary-effort adaptation is useless, that Incremental Backups should lose the R39 gain, or that all content-derived effort policies are too narrow.

## Reopening predicate

Do **not** reopen R40 by sweeping dictionary levels, text-extension subsets, file-size thresholds, workload/path allowlists or hashes.

A superseding experiment is justified only by new causal evidence that changes the carrying-cost model, for example:

1. a generic already-required encoder signal can subsume the R39 effort choice without adding a new long-lived policy branch; or
2. independent structural-transfer evidence shows materially larger opportunity for the same causal family outside the one backup row; or
3. a concept-compressed effort scheduler replaces multiple existing effort choices, making the R39 behavior a consequence of a broader canonical rule rather than an extra exception.

Any such experiment requires a new preregistration; R40's grammar, corpus, thresholds and interpretation remain immutable.

## Forge decision and next action

**Do not productize the present `family-dict9` predicate. Preserve the R39 local win and attack its exported portfolio-entropy debt.**

The next cheapest decisive work is R0/D2–D3 concept-compression analysis: inspect whether the information already computed by canonical candidate selection contains a generic, operation-owned measure of marginal dictionary effort/value that can express the R39 choice while also replacing or subsuming another existing effort decision. The target is not to discover a broader benchmark allowlist. The target is to make the protected R39 behavior fall out of a simpler general rule with zero or negative net policy-branch carrying cost.

If no such pre-existing semantic owner exists, retain R39 as scoped positive evidence and R40 as the product-negative boundary; do not spend a new deep run on scalar tuning of the same family.

## Strongest surviving self-critique

R40's AOM estimate is a **15-workload public-matrix proxy**, not a proof about the world's data distribution. The matrix is deliberately heterogeneous but finite. Therefore the correct conclusion is not “this family can never matter.” The correct conclusion is narrower and stronger: **the evidence currently available does not justify making this exact extra policy branch part of a general-purpose product.** New independent transfer evidence could reopen that conclusion, but closeness on the original backup target cannot.

A second measurement caveat is that the aggregate `runtime_vs_dict12` count includes non-activating workloads whose identical behavior differs only by timing noise. It is useful as raw hostile-review telemetry but must not be interpreted as evidence that dict9 speeds six unrelated workloads. The causal runtime claim remains confined to the workload where the family actually activates.

## Release boundary

R40 is diagnostic/Hostile-Reviewer evidence only. It grants **zero** release credit, does not change canonical product policy, does not alter the 687,783-byte hurdle, and does not satisfy final exact-head release authority.

**v0.30 remains MERGE / TAG / VERSION / PUBLISH LOCKED.**

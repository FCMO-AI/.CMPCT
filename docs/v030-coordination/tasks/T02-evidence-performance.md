# T02 — Authoritative evidence / performance / competitor matrix

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** final authority must run on the exact reconciled product candidate after T01/T03 behavior is final.

## Objective

Turn v0.30 from promising mechanism evidence into exact release evidence without lowering any threshold, mixing independent savings, or treating pre-product/pre-fingerprint runs as release authority.

## Selective-read measurement contract

Earlier review found two measurement defects that must remain fixed:

1. locality may not be derived from a missing flattened build statistic with a `0.0x` default;
2. genuine r24 fallback supports the canonical public `read_member` operation and therefore must be measured rather than called “not applicable.”

Required invariant:

- derive normative locality from the **actual member operation's returned stats** and cross-check archive/build declarations when present;
- missing locality/accounting data on an r25 member read is a hard evidence failure;
- measure the canonical product member API for both r24 and r25;
- choose the largest regular user-visible member, excluding internal manifests and alias-only entries;
- preserve exact member SHA/length, fresh-process timing, raw RSS, and <=8x decoded-context accounting;
- keep contract tests proving omitted locality cannot default to a passing value and r24 fallback reaches a true member-read operation.

Footnote: a build-time declaration is corroboration, not a substitute for observing the operation the release claim is about.

## Ablation / benchmark semantics contract

Earlier review found a historical-vs-product semantic mismatch in the causal ablation harness. The repaired design must remain separated into two ledgers:

1. **Frozen research-frontier causality:** preserve the accepted repair-v6 15-workload source trees and exact accepted-v0.29 identity `137,499,525 B`; run v0.29 / Geometry / PrefixGraph / combined under those historical content-tree semantics so the immutable threshold remains comparable. The superseded pre-repair aggregate `137,501,815 B` remains historical provenance only and is not an accepted current baseline.
2. **Canonical product parity:** compare genuine canonical v0.29/r24 product bytes against canonical v0.30 product bytes on the same original filesystem trees, including r25 filesystem-manifest semantics and genuine r24 fallback.

A manifest-charged causal ablation is allowed only if every variant uses the same prepared tree and identical metadata charge. It must be labeled as a new causal substrate and may not claim reproduction of the historical baseline unless it actually does.

Combined exact-minimum assertions may compare only complete artifacts with equivalent semantics. Independent research savings must never be added together as if they were a product result.

Preserve the frozen >=687,783 B, >=3 improved, zero-regression, and <=8x gates on their accepted substrate. Add stricter product parity rather than moving those goalposts.

Footnote: r25 is allowed to pay a genuine new filesystem framing cost. Benchmark honesty requires charging it; historical v0.29 bytes may not be retroactively redefined to make that cost disappear.

## CI-topology contract

The v0.30 workflow set must satisfy current repository topology policy:

- mechanism/oracle experiments are `deep`;
- final compression/runtime/native/external evidence is `release`;
- `fast` is reserved for genuinely ordinary PR feedback;
- deep/release PR-triggered workflows use meaningful path scope or a cleaner branch/dispatch trigger;
- concurrency cancellation and every numeric threshold remain unchanged;
- run `python tools/check_ci_topology.py` over the complete active v0.30 workflow set before final handoff.

An earlier repair classified the coordinator-listed workflow set and fixed the first missing-lane failures. Final evidence must use the current exact branch state; old topology greens are not enough if workflows changed afterward.

## Scope

- repaired exact 15-workload generalization suite;
- v0.29 / Geometry-only / PrefixGraph-only / combined complete-artifact ablations;
- canonical r24-vs-r25 product parity;
- shared-build rehabilitation and duplicate-work accounting;
- controlled create/extract/selective-read/peak-RSS measurements;
- external competitor matrix: ZIP/Deflate, 7z/LZMA2, solid tar+Zstd-19, ZPAQ m5 where available;
- exact-tree extraction verification for every credited competitor;
- CI routing/evidence artifact harvesting for the current exact candidate;
- durable accepted records under `benchmarks/history/` only after gates are genuinely satisfied.

## Frozen gates

Do not weaken:

- accepted v0.29 aggregate identity;
- >=687,783 B aggregate saving;
- >=3 improved rows;
- 0 byte-regressed rows;
- <=8x selected per-member decoded-context amplification;
- shared-build >=20% and >=5 s rehabilitation hurdle where defined;
- runtime ratios/noise policy already frozen by release gate;
- symmetric benchmark semantics and exact-tree verification.

## Preferred implementation area

Prefer `benchmarks/v030_*`, v0.30 benchmark tests, release/deep workflows, and durable evidence records after acceptance. Because one executor owns the release, implementation bugs exposed by benchmark evidence may be fixed directly in the owning product/native code; the benchmark threshold or workload semantics must not be changed to hide the defect.

## Completion evidence

1. Current candidate reproduces every frozen input tree and exact historical v0.29 bytes.
2. Complete candidate aggregate passes frozen compression/locality gates.
3. Genuine canonical product r25 never exceeds genuine r24 on the same original filesystem tree; exact ties retain r24.
4. Controlled repeated runtime/RSS gate passes or preserves explicit regression debt with exact failing rows.
5. External competitor matrix verifies extraction semantics before crediting archive size and preserves every fair loss.
6. CI artifacts/runs are tied to the exact reconciled candidate fingerprint/SHA; queued/cancelled/superseded runs are not counted.
7. Accepted results are committed durably with raw measurements/provenance sufficient to regenerate public claims.
8. Historical causality and canonical product parity remain visibly separate; neither silently substitutes for the other.
9. Selective-read locality comes from observed member operations, with no missing-field default that can pass a normative gate.
10. Current v0.30 workflow topology checker is green without weakened thresholds.

## Failure behavior

If a gate fails, preserve the machine result and keep T02 `CLAIMED` while fixing the underlying release defect, or document explicit breakthrough regression debt when repository policy permits rehabilitation. Never tune the workload, timing boundary, threshold, or comparator to turn red into green.

## Prior implementation checkpoint retained as provenance

Earlier work repaired the three review blockers above:

- `benchmarks/v030_perf_worker_canonical.py` instruments the actual canonical public `read_member` call in the same fresh process and reports observed decode context for Geometry, PrefixGraph, and genuine r24 fallback;
- `benchmarks/v030_release_selective_read_canonical.py` measures selected canonical product profiles, chooses the largest regular user-visible member, excludes internal r25 manifest/alias kinds, verifies exact SHA/length, preserves wall/RSS measurements, and enforces the unchanged <=8x law;
- `benchmarks/v030_release_ablation_canonical.py` emits separate `historical_causality` and `canonical_product_parity` ledgers with substrate identities and rejects cross-substrate exact-min arithmetic;
- the v0.30 workflows were classified for CI topology and the topology checker was added to the evidence path.

Earlier lineage included commit `2ff883ea41f2c70fb3cd7151de5be7639f4069b5` and integration ancestor `f6a273bbb1e49e21096a1cc875eff35a8e3c1110`. Those SHAs are mechanism provenance only. Final product parity, selective-read, runtime, competitor, and topology authority must be rerun on the exact frozen authoritative candidate.

## Superseded exact-fingerprint gap ledger — 2026-09-03

The prior release-critical fingerprint `8abe67c6c9a93e72eeed61dba13cfc990c21652c43749dfa36d213b658c8358e` remains historical provenance only. The authoritative generalization workflow itself later required a release-critical Custody correction, so receipts from this older fingerprint may not authorize the current candidate.

## Current exact-fingerprint release gap ledger — 2026-09-04

The authoritative generalization custody repair at commit `2b67c94c5277699fdfa42b2e09651fa640b0552c` changed a fingerprinted workflow without changing any benchmark, threshold, corpus, locality rule, timing envelope or product-selection law. The current release-critical fingerprint is now:

`c119dbae83a8eae6d09dbf48e764a4bc9679452cef4381cb031dc3444ecfbc69`

The coordination/evidence/receipt commits that followed are intentionally outside fingerprint scope; they do not mutate candidate bytes or this fingerprint.

Current-fingerprint T01 evidence has been regenerated rather than rebound from history:

- native authority run `33871978882`, exact source `631216979c01627a8a3bc2bc598327c4f065e6ca`, emitted `c119dbae...fbc69` and passed canonical Python/Rust boundaries, builder-independent goldens, native/implicit-v4 recovery, r24 fallback strong verification, Logs native parity/semantics and shared-core use;
- ZIP portability run `33871978857`, the same exact source and fingerprint, passed stock ZIP tree parity, r24 fallback export, G04 export, PrefixGraph export and atomic publication;
- both strict JSON artifacts are now persisted under `docs/v030-release-evidence/` and the `native-r25` / `zip-portability` receipts bind their exact evidence hashes to `c119dbae...fbc69`.

Those wins do **not** close T02 and do not make T01 DONE; Android/physical-platform evidence is still separate.

The required T02 closure set remains exactly:

- `compression-generalization`: accepted-v0.29 `137,499,525 B`, saving >=`687,783 B`, >=3 improved, 0 regressions, <=8x selected-member amplification, exact tree and v0.29-row identity;
- `shared-build-rehab`: byte-identical, >=20% and >=5 s wall improvement, one attempt-5 graph build;
- `runtime-memory-selective`: median create/extract <=1.10x, max workload create/extract <=1.25x, peak RSS <=1.25x, selective read actually measured;
- `external-competitors`: exact-tree/symmetric-semantics/hostile-frontier/fair-loss facts plus strict no-tie wins over ZIP and Zstd-19 in size and create on every required workload;
- `ci-topology`: all v0.30 workflows classified, topology checker green, thresholds unchanged.

On the T01 coordination-only source delta, the push-side authoritative-generalization run `33871978793` passed only its impact classifier and deliberately skipped the result-bearing `release-generalization` job. Runtime/RSS run `33871978831` likewise skipped both result-bearing jobs, and hostile mutation run `33871978866` skipped `release-fuzz`. These classifier greens are not receipts. Obtain deliberate result-bearing current-fingerprint runs through existing dispatch/control surfaces; do not change release-critical source or thresholds merely to wake CI.

Move T02 to `DONE` only after every release-lock evidence obligation above is durably closed on `c119dbae...fbc69`.

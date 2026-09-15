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

## Exact-head authority-v2 runtime diagnosis — 2026-09-15

The preserved runtime artifact from authority-v2 run `34919975890` has now been inspected directly rather than inferred from job status. `runtime-v2.json` and its process-tree RSS companion agree on the important owners.

The ordinary self-RSS measurement initially appeared red because it measured only the parent process: shifted versions reported v0.30/v0.29 pack RSS `2.1099x`. The process-tree companion corrects that custody error and shows the real peak-RSS gate **passes**: shifted `0.9538x`, logs `0.6295x`, ML `0.7297x`, aggregate max `1.0x`. Do not spend product effort on the superseded parent-only RSS signal.

The real remaining runtime debt is concentrated in two places under unchanged gates:

- **ML (`09_ml_artifacts`, selected `geometry-g04`)**: median create `1.4162x` in process-tree evidence (`~37.9 s` v0.30 vs `~27.3 s` v0.29) and median extract `2.0339x` (`~0.181 s` vs `~0.090 s`). This row alone violates the `1.25x` per-workload create/extract ceilings and is the dominant product owner.
- **Logs (`05_logs_and_telemetry`)**: creation is dramatically faster (`~0.0085x`) but extraction is `1.3342x` (`~0.051 s` vs `~0.038 s`), so it violates the per-workload extract ceiling and also makes the three-row median extract ratio `1.3342x`, above the `1.10x` median ceiling.
- **Shifted versions** is not a runtime blocker in the process-tree receipt: median create `1.0585x`, extract `0.9101x`, RSS `0.9538x`.

All three rows remained byte-nonregressing in the preserved receipt. The ML row still buys `161,614 B` in the process-tree run and shifted buys `22,390 B`; logs buys only `264 B`. Therefore the next repair should not indiscriminately disable r25/G04: ML has material byte value that must be rehabilitated, while logs has a very small byte margin and deserves a stricter carrying-cost/admission analysis if its extraction debt cannot be removed cheaply.

A separate research diagnostic intended to attribute ML extraction cost was found to wrap the shipping `PRODUCT.build/extract` route in the private `_revision25_profile_context()`. That is not how `benchmarks/v030_perf_worker_v2.py` exercises the product and the diagnostic previously failed to reach extraction within a 15-minute envelope even though authority-v2 builds ML in roughly 38 seconds. Treat that profiler as contaminated until it is rerun through the unwrapped shipping front door; do not optimize from its timeout/checkpoint.

**Next executable target:** first repair the ML extraction profiler so it observes the exact shipping route, then use its function-level ownership to attack the ~2.03x extraction debt without weakening authentication/restoration semantics. In parallel only if independent, inspect ML G04 creation build stats for the ~10.6 s excess over v0.29. Logs extraction is the next product lane after ML ownership is established. Runtime-memory-selective remains open; v0.30 remains merge/release locked.

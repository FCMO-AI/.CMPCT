# r25 post-isolation diagnostic revalidation result

Status: **ACCEPTED CUSTODY / SCOPED INSTRUMENT INVALIDITY / PRE-ISOLATION REVALIDATION RETIRED / NO RELEASE CREDIT**

This record preserves what the unchanged-candidate revalidation wave learned from two historical Shifted RSS diagnostics after PrefixGraph process isolation became the shipping mechanism. It does **not** revise either frozen historical experiment or its accepted result. It changes no production source, candidate bytes, archive grammar, selector, locality bound, integrity/recovery rule, benchmark threshold, release threshold or release state.

## Current authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact revalidation source head: `5a316cdce29350a418d9c01cdc644ebec73bc21f`;
- release-critical candidate fingerprint witnessed by the same-head hosted Android artifact: `953a94e15662a5bee5e92596806a4c33cb5bce26a243a63121f7763bdd423e11`;
- shipping PrefixGraph executor: `experiments.entropygraph_v030_prefixgraph_process_executor.PrefixGraphProcessExecutor`;
- shipping scheduler: exact private PrefixGraph owner executes synchronously in a bounded child, that child exits, then G0-G4 begins in the parent;
- release credit from this record: **false**.

The historical accepted results remain authoritative only for the regimes they actually tested:

- `R25_PRODUCT_LIFETIME_RSS_PHASE_RESULT.md`: valid on source `b02b4ad06d07025de6e9a0fd8ad64e283df42fd2`, when both candidate builders were parent-observable and simultaneously active at the measured high-water;
- `R25_CANDIDATE_RECLAIM_RSS_RESULT.md`: valid on source `5f2633c016304f4743359fb841727c10c85628b6`, on the frozen serialized in-process PrefixGraph-before-G0-G4 seam.

Neither result is rewritten by the current revalidation.

## Revalidation 1 — product-lifetime phase attribution

Workflow `CMPCT v0.30 product-lifetime RSS phase attribution`, run `33772287606`, substantive job `100705858731`, uploaded artifact `9900477326` with ZIP digest `sha256:d16f0d29d2a3c507a1ed8a200500744b74ac2009680149021d842b779db071f4`.

The three fresh-process repetitions completed the shipping build cleanly and reproduced one exact product identity:

- selected representation: `prefixgraph`;
- complete selected bytes: **1,700,666 B**;
- genuine r24 bytes: **29,883,732 B**;
- strong verification: passed;
- sampler errors: zero;
- sampled-live-RSS / process-`ru_maxrss` coverage: approximately **1.0014 / 1.0007 / 1.0009**.

The instrument nevertheless returned `experiment_valid=false`, decision `INVALID`. Its frozen validity grammar requires both exact `g04-build` and exact `prefixgraph-build` entry phases to be observed in the measured process. All three repetitions observed G0-G4 entry (about **188,888–190,052 KiB**) but `prefixgraph_entry_vmrss_kib` was `null` in every repetition.

This is causal instrument invalidity, not a product-memory loss. The frozen worker monkeypatches the parent process's private PrefixGraph `build` callable. The shipping scheduler now executes that semantic owner inside `PrefixGraphProcessExecutor`'s child process, so the parent hook cannot observe the required child entry by construction. The old retained-entry estimator therefore cannot be evaluated under the new lifetime boundary without changing its scientific grammar.

## Revalidation 2 — serialized candidate reclaim RSS

Workflow `CMPCT v0.30 candidate reclaim RSS attribution`, run `33772287597`, substantive job `100705610613`, uploaded artifact `9900538913` with ZIP digest `sha256:fa0445b53d49b30a788c226f933e5b11867d56625b717a58de7d2604648cd522`.

All **9/9** frozen fresh-process arms (`control`, `gc`, `trim`, three each) failed before any decision-bearing reclaim comparison. Every worker stopped on the same validity assertion:

`RuntimeError: frozen PrefixGraph serialization seam was not exercised exactly once`

The terminal evidence is therefore `experiment_valid=false`, decision `INVALID`, with no summaries or derived treatment effects. Again, this is not a negative result for GC, allocator trimming, PrefixGraph, or shipping memory. The frozen experiment intercepts a historical in-process serialization seam that the current shipping path replaced with the supported one-shot child lifetime boundary.

## Causal interpretation

Both failures are the expected consequence of a successful later Forge intervention: the system under test changed in exactly the dimension these old diagnostics instrumented. Re-running them automatically on the current product is therefore not scientific replication. It asks frozen instruments to observe execution seams that no longer exist.

The current product-memory authority is the superseding external process-tree measurement and the completed PrefixGraph isolation S6 productization evidence. Those measurements charge child memory rather than gifting it away. Historical diagnostics remain useful for explaining why process isolation was pursued, but their current-head `INVALID` revalidations receive zero release credit and zero negative-evidence credit.

## Forge / Custody decision

**`PRE_ISOLATION_RSS_DIAGNOSTIC_REVALIDATION_RETIRED_ON_SHIPPING_HEAD`**

1. preserve both historical frozen experiments and their accepted historical results unchanged;
2. preserve the two current-head invalid artifacts as scoped evidence that their observation seams are obsolete;
3. do **not** repair either frozen v1 instrument in place;
4. do **not** interpret these red workflow conclusions as a shipping RSS regression;
5. do **not** spend another activation building successor phase/reclaim diagnostics unless current product-authority memory becomes red or a concrete unresolved allocation owner again blocks release;
6. when release-critical revalidation is no longer in flight, make the historical workflows manual/historical-only or otherwise prevent automatic shipping-head reruns, without deleting reproducibility.

The last point is deliberately deferred while the same candidate fingerprint is undergoing expensive exact-authority revalidation: changing a `v030-*.yml` workflow is inside the strict release fingerprint and would invalidate the in-flight receipt wave merely to silence known diagnostic noise.

## Reopening predicate

A superseding child-aware phase or reclaim experiment becomes justified only if at least one of the following becomes true:

- the exact product whole-process-tree RSS authority exceeds its frozen release ceiling;
- PrefixGraph process isolation is removed or materially changes lifetime semantics;
- a new exact product measurement identifies an unresolved current-shipping memory owner for which phase attribution would change the next intervention;
- platform evidence shows a child-lifetime memory failure hidden by the existing product matrix.

Absent one of those conditions, a new phase/reclaim instrument would be measurement churn rather than Forge convergence.

## Strongest self-critique

This record retires **automatic applicability**, not the historical causal facts. The old experiments remain reproducible and valid for their original source regimes. Conversely, the current invalid reruns do not prove the present product is memory-optimal; they only prove these two specific pre-isolation observation seams cannot answer that question anymore. Current shipping memory must continue to be judged by child-aware whole-process-tree authority and platform evidence.

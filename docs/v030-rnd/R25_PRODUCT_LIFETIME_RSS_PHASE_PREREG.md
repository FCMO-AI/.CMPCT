# r25 product-lifetime RSS phase attribution preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE R0 DIAGNOSTIC / NO RELEASE CREDIT**

This experiment follows the accepted product-phase, exact-semantic-owner, candidate-scheduling-v3 and outer-product-scheduling results. Those predecessors are immutable. In the tested Shifted regime they respectively show that profile capture alone is not the dominant RSS owner, neither exact G0-G4 nor exact PrefixGraph alone reproduces the shipping peak, serializing their inner overlap makes RSS/wall time worse, and serializing the outer genuine-r24/r25 race removes only 9.9863% of peak RSS—below its frozen 10% primary-owner boundary.

## Forge diagnosis

- strict target: `resemblance_hostile_v1 / 01_shifted_versions` RSS rehabilitation while preserving the shipping byte gain and every release invariant;
- diagnosis: **D2 unresolved product-state/lifetime ownership**, with R0 measurement required before a Builder change;
- radicality: **R0**;
- saturation: **S2** applies to scheduler permutations: two material scheduling experiments failed to establish scheduling as the dominant owner, so another scheduler permutation is not the primary path;
- release credit: **none**.

Worldview under test:

> The remaining shipping RSS excess is caused either by substantial product-owned state already resident when the exact r25 candidate builders begin, or by a later labeled product phase outside the candidate builders. A phase-labeled live-RSS trace can distinguish those cases without changing production behavior.

## Frozen target / identity

- deterministic suite/workload: `resemblance_hostile_v1 / 01_shifted_versions`;
- accepted repaired historical source tree must match before measurement;
- three independent fresh-process repetitions;
- exact shipping `experiments.entropygraph_v030_release_product.build` is the measured operation;
- each repetition must produce the same selected complete archive bytes/SHA-256 and strongly verified canonical filesystem tree;
- exact canonical PG/G0-G4/reader semantic-owner identities must be asserted;
- Linux `/proc/self/status` `VmRSS` is the live-resident diagnostic; process `ru_maxrss` remains the authoritative total high-water observation and is never replaced by sampled RSS.

## Frozen observation seams

The worker may wrap functions only to enter/exit named observation phases; wrappers may not change arguments, results, scheduling, exceptions or production source. Every binding must be restored after the measured build.

Required phases:

1. `shipping-product` — entire promoted `product.build` call;
2. `profile-prepare` — canonical profile-tree preparation;
3. `r24-prebuild` — the actual release-product locality-bounded r24 build used by the prebuild overlap;
4. `r24-consume` — canonical r24 floor consumption/build seam;
5. `r25-tournament` — canonical `_r25_build`;
6. `g04-build` — exact canonical G0-G4 semantic owner;
7. `prefixgraph-build` — exact canonical PrefixGraph semantic owner;
8. `strong-verify` — canonical selected-product strong verification inside the shipping build.

A dedicated sampler thread records only phase-combination peaks at **10 ms** intervals plus exact enter/exit event snapshots. It must not retain every sample. The monitor begins immediately before `product.build` and ends immediately after it returns, before the independent post-measurement correctness verification.

## Frozen validity rules

Evidence is valid only if:

- all required wrappers were installed on the exact shipping resolution objects and restored afterward;
- production source files are unchanged by the instrument;
- no executor/scheduler/admission/selector/grammar/integrity/recovery/locality threshold is patched;
- all three fresh-process workers succeed and preserve exact product identity;
- sampler errors are empty and each repetition has at least 100 live samples;
- sampled peak `VmRSS` reaches at least **90%** of the same process's `ru_maxrss`; otherwise the sampler is too coarse to locate the high-water phase and the result is invalid rather than reinterpreted;
- both exact candidate phases are observed on the preregistered PrefixGraph-eligible Shifted target.

## Frozen retained-entry quantity

For each repetition:

- `B` = live `VmRSS` immediately before the measured shipping operation;
- `P` = maximum sampled live `VmRSS` during the shipping operation;
- `E` = the **minimum** live `VmRSS` observed at entry to `g04-build` or `prefixgraph-build` (the first candidate-entry baseline, before the later candidate can inherit allocations made by the earlier one);
- `retained_entry_fraction = max(0, E - B) / P`.

Using the minimum candidate entry deliberately prevents concurrent work by the first candidate from being mislabeled as pre-existing retained product state.

## Frozen decision rule

First locate the sampled global-peak phase combination in every repetition.

1. If the peak occurs **outside both `g04-build` and `prefixgraph-build` in at least two of three repetitions**, candidate construction is not the immediate peak-owning phase. Advance directly to the consistently observed later/earlier product phase; do not alter candidate scheduling.
2. Otherwise use the median `retained_entry_fraction` across all valid repetitions:
   - **>=20%**: support substantial pre-candidate retained product state as a material owner; next freeze an A/B that removes or releases the identified retained class without changing product bytes.
   - **<10%**: retire pre-candidate retained state as the primary explanation; the excess is generated mainly during/after candidate execution and the next instrument must compare product-context versus isolated candidate lifetime/temporary buffers.
   - **10% to <20%**: ambiguous; no Builder intervention. Narrow the observation seam before changing production.
3. If peak phase ownership is inconsistent across repetitions, return `AMBIGUOUS_PHASE_OWNERSHIP` regardless of the retained fraction.

The 20%/10% bands are causal allocation thresholds, not release RSS tolerances. The release lock remains unchanged.

## Hard invariants

No representation, byte accounting, source corpus, accepted-v0.29 floor, genuine-r24 floor, candidate eligibility, selector, verification, recovery, integrity, locality/decode-unit limit, platform requirement, competitor setting, RSS threshold, release receipt or publication state changes. `release_credit=false` is mandatory.

## Negative-evidence law / next action

Preserve the exact phase result even if it falsifies the retained-state hypothesis. A loss retires only the tested ownership explanation. It does not justify weakening RSS or tuning away the proven r25 byte gains. The next action is the narrowest causal A/B named by the frozen decision above.

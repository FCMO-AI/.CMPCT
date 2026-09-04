# r25 serialized candidate reclaim RSS preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE R0 DIAGNOSTIC / NO RELEASE CREDIT**

This experiment follows the accepted product-lifetime phase attribution in `docs/v030-rnd/R25_PRODUCT_LIFETIME_RSS_PHASE_RESULT.md`. That result located the Shifted shipping high-water during simultaneous exact G0-G4 + PrefixGraph construction and retired pre-candidate retained state as the primary owner at a frozen 9.6271% retained-entry fraction. Earlier scheduler evidence also showed that naive serialization worsened RSS and wall time, so this experiment does not propose serialization as a product fix.

## Forge question

Under the already-tested serialized diagnostic seam, PrefixGraph finishes before G0-G4 begins while its exact result remains available for later winner selection. The v3 serialized arm still reached a larger process high-water than shipping. That leaves two materially different explanations:

1. **live semantic retention** — the completed PrefixGraph result/object graph itself is large enough that G0-G4 must overlap it in memory; or
2. **reclaimable candidate-produced retention** — temporary Python/native/library allocations from the completed PrefixGraph build remain resident/allocator-owned after its result is produced even though they are no longer semantically required.

The experiment measures that boundary before any production source change.

## Frozen target and identity

- target: `resemblance_hostile_v1 / 01_shifted_versions` from the accepted repaired corpus;
- exact accepted historical source-tree identity required;
- exact canonical PG/G0-G4/reader semantic-owner identity required;
- the final complete selected archive bytes, physical SHA-256, selected representation and verified canonical filesystem tree must be identical across every valid arm/repetition;
- release credit is always false.

## Frozen arms

All arms force only the previously frozen **diagnostic serialized PrefixGraph-before-G0-G4 seam** by replacing the one PrefixGraph executor with an inline executor. Candidate eligibility, candidate code, admission, selection, verification, archive grammar and result values are unchanged.

Each arm retains the completed PrefixGraph return object exactly until the shipping selector is finished.

1. `control` — no reclamation action between PrefixGraph return and G0-G4 entry.
2. `gc` — call Python `gc.collect()` after PrefixGraph returns, while retaining its exact return object.
3. `trim` — call `gc.collect()` and then Linux/glibc `malloc_trim(0)` after PrefixGraph returns, while retaining its exact return object. If `malloc_trim` is unavailable the experiment is invalid rather than silently substituting another allocator operation.

The trim arm is **diagnostic only**. It does not authorize glibc-specific production behavior. A positive result would justify a portable lifetime intervention such as candidate process isolation or targeted removal/release of a measured temporary allocation class.

## Frozen measurements

For every fresh-process worker record:

- live `VmRSS` immediately after PrefixGraph returns and before reclamation;
- live `VmRSS` after the arm action and immediately before G0-G4 begins;
- complete process `ru_maxrss` across the shipping build;
- shipping wall time;
- recursive Python `sys.getsizeof` census of the retained PrefixGraph result object, with cycle protection (diagnostic only; it does not count native allocator state);
- exact final archive identity and strong verification.

Run three repetitions per arm in deterministic alternating order:

`control,gc,trim / trim,gc,control / control,trim,gc`.

`ru_maxrss` is the decisive peak metric. `VmRSS` and object-graph size are causal diagnostics only.

## Frozen derived quantities

For each arm, use median values over three valid repetitions.

- `peak_reduction_fraction(arm) = max(0, median_control_ru - median_arm_ru) / median_control_ru`;
- `entry_reclaim_fraction(arm) = max(0, median_pre_action_vmrss - median_post_action_vmrss) / median_control_ru`;
- `retained_result_fraction = median_prefixgraph_result_deep_bytes / (median_control_ru * 1024)`.

No baseline subtraction may replace the complete-process peak.

## Frozen decision

Evidence is valid only with zero worker failures, exact cross-arm product identity, exact semantic-owner identity, successful strong verification and exactly three repetitions per arm.

Decision precedence:

1. If `gc` reduces median process peak by **>=20%**, return `PYTHON_GC_RECLAIMABLE_OWNER_SUPPORTED`.
2. Else if `trim` reduces median process peak by **>=20%**, return `ALLOCATOR_TEMPORARY_RETENTION_SUPPORTED`.
3. Else if both `gc` and `trim` reduce median process peak by **<10%**, return `GENERIC_RECLAIM_RETIRED_AS_PRIMARY`.
4. Otherwise return `AMBIGUOUS_RECLAIM_OWNERSHIP`.

The 20%/10% bands are causal ownership thresholds, not release tolerances. The v0.30 release RSS ceiling remains unchanged.

A `*_SUPPORTED` decision is still R0 evidence only. It does not authorize a Builder change until the measured class is translated into the lowest-sufficient portable R1/R2 intervention and that intervention is tested against the unchanged full runtime/RSS/selective-read gate.

## Hard invariants

This experiment changes no production source, format revision, representation bytes, candidate eligibility/admission, selector, locality/decode-unit law, integrity/recovery behavior, accepted-v0.29 floor, genuine-r24 floor, competitor setting, benchmark threshold, release receipt or publication state. Exact selected archive identity is mandatory.

## Negative-evidence law

A loss retires only generic post-PrefixGraph reclamation as the primary explanation under this exact serialized Shifted regime. It does not imply that all candidate-lifetime work is futile and does not permit tuning away r25 byte gains. A losing result should next isolate **live result/object ownership or specific retained buffers** rather than another scheduler permutation.

# ONE-G0.2 compact observer handoff — hostile review before evidence

Date: 2026-09-08

## Scope

This review occurred after preregistration and implementation but **before consuming any result from the dedicated compact-observer handoff workflow**. Its purpose is to remove test-design mistakes, not to tune a disappointing result. The frozen 0.90 advancement threshold, 1.05 no-regression ceiling, 15 repetitions, 1 MiB voting scale, semantic gates, and 2-of-3 opportunity-rich rule are unchanged.

## Defect 1: `near_repeats` accidentally encoded exact chunk reuse

The first generator repeated the same 64-byte motif and damaged only sparse positions. Because the observer's exact-reuse fingerprint chunk is also 64 bytes, most aligned chunks were literally identical. A workload intended as a low-opportunity resemblance-like control would therefore have been transformed into a high exact-reuse fixture by generator alignment.

That weakens the falsifier: the compact candidate is expected to benefit most when many Python opportunities would otherwise be materialized, so allowing the negative control to become opportunity-rich makes the no-regression gate easier rather than harder.

### Correction before evidence

Each 64-byte near-repeat chunk now starts from the same motif but carries a unique 64-bit block id plus one deterministic varying byte. Chunks remain visibly/structurally similar, but they are no longer identical fixed-chunk reuse candidates merely because of the generator. A semantic test asserts that `random` and `near_repeats` produce at most eight total exact run/reuse opportunities at 64 KiB, while `structured` and `long_runs` positively exercise observer opportunities.

This is a premise repair, not a threshold change. Any workflow result from a pre-repair SHA is inadmissible for the advancement decision.

## Defect 2: modeled native output widths used literal `24`

The first benchmark reported eager-arm modeled native output capacity/usage by multiplying opportunity counts by 24 bytes. That matches the current three-`uint64_t` structs on the present ABI, but it bakes an ABI assumption into evidence metadata.

### Correction before evidence

The benchmark now imports `_CRun` / `_CReuse` from the same native wrapper and uses `ctypes.sizeof` for both capacity and used-byte accounting. This does not affect timing or decisions; it prevents metadata from becoming silently wrong on a different ABI.

## Remaining hostile limitations intentionally retained

1. **The candidate retains worst-case native arrays through the writer.** The eager path discards those arrays when it returns the Python graph. This may make the compact path faster but more memory-hungry. The benchmark records capacity/used bytes but does not claim peak RSS. A subprocess RSS measurement is mandatory before product promotion.
2. **Current admission/segmentation still consume source/target directly.** Therefore an ADVANCE result only proves that eager Python observer materialization is unnecessary overhead in the present charged writer envelope. It does not yet prove a fused observe→admit→segment design or that downstream Law discovery consumes the compact opportunities.
3. **`compressed_like` is not required to be opportunity-rich.** It remains one of three target rows because already-compressed/codec-like material must stay in the hostile matrix; advancement still requires only two of the three target rows to clear 0.90. `structured` and `long_runs` are premise-checked positive-opportunity rows.
4. **Source/target ctypes buffers and a worst-case segment buffer are allocated outside paired timing.** This matches the existing writer profiling boundary and isolates the observer-handoff question. It is not a total process-startup/RSS result.
5. **Python object teardown is excluded symmetrically.** Prior same-arm writer results are released before the next timer starts so destruction of the previous graph cannot contaminate the next arm.

## Evidence rule

Only a dedicated workflow run whose `EVIDENCE_HEAD` contains both this review and the corrected benchmark/tests may decide among:

- `ADVANCE_COMPACT_OBSERVER_HANDOFF`
- `HOLD_COMPACT_OBSERVER_HANDOFF`
- `INVALIDATE_COMPACT_OBSERVER_HANDOFF`

No pre-repair run may be used, even if its result is more favorable.

# ONE Genesis candidate-boundary enforcement preregistration — 2026-09-10

**Mission Lock / Referee:** prevent the sealed Genesis executor from running a CMPCT1 product surface that the repository has not explicitly certified as the general ONE contender.

## Observed defect

`benchmarks/one/genesis_one_candidate_boundary_v1.json` currently states `HOLD_UNTIL_COMPLETE_PRODUCT_BOUNDARY_IS_CERTIFIED`. The current CMPCT1 fresh-process worker nevertheless hardcodes `experiments.one.general_law_archive` for creation and `experiments.one.authenticated_archive_envelope` for reads. Calendar/executor authorization alone can therefore reach a surface that the candidate-boundary authority itself says is not yet eligible.

This is a gate-integrity defect, not a compression-result defect. No Genesis workload needs to be executed to falsify it.

## Hard invariant

A real Genesis CMPCT1 worker invocation must fail closed unless a repository manifest explicitly certifies the exact creator and reader surfaces that worker will invoke. Transfer/synthetic fixture operation remains legal and must not become production evidence.

Certification must be source-bound and machine-readable. A date boundary, environment authorization marker, or runnable module is insufficient by itself.

## Falsifiable hypothesis

If the CMPCT1 product worker verifies the candidate-boundary manifest before loading any ONE product surface, then executor authorization cannot accidentally promote a mechanism-only, Surprise-only, or otherwise uncertified surface into the Genesis contender.

## Disproof tests

The change is rejected if any of these is possible:

1. production authorization succeeds while the manifest status remains HOLD;
2. production authorization succeeds when the manifest certifies a different creator or reader path than the worker imports;
3. transfer-fixture tests become labeled production-eligible or require production certification;
4. the enforcement path executes, compares, scores, or inspects the 15 Genesis workloads;
5. future certification can be achieved only by weakening or deleting the existing anti-cherrypick rules.

## Acceptance evidence

- unit test proving an otherwise-authorized production worker fails while the current manifest is HOLD;
- unit tests for wrong/missing certified surface identity;
- existing transfer fixture exact build/whole/selective tests stay green;
- no workload generation, contender comparison, scoring, or winner selection is added;
- the candidate-boundary manifest remains the sole authority for whether the hardcoded ONE product surface is eligible.

## Non-goals

This change does **not** certify the current `general_law_archive` / `authenticated_archive_envelope` pair. It does not choose the final ONE contender. It does not modify v0.29/v0.30, the 15-workload authority, thresholds, or measurement semantics. Certification requires separate evidence and a deliberate manifest update.

## Hostile-review question after implementation

Can any caller reach `_load_surface()` in production mode while the manifest is HOLD or names different product files? If yes, this preregistration fails.

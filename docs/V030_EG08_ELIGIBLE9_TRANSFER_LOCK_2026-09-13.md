# v0.30 EG08 adaptive-effort eligible9 transfer — mission lock

Date: 2026-09-13
Status: preregistered transfer on the independently mapped EG07-valid domain.

## Frozen domain

`docs/V030_EG07_TRANSFER_ELIGIBILITY_RESULT_2026-09-13.md` mapped the transfer domain using EG07 only, before consulting EG08 transfer results. Exactly nine deterministic surfaces are valid under the unchanged parent representation and frozen locality/decode contract:

Neutral/current15:

- `02_office_workspace`
- `04_analytics_and_database`
- `05_logs_and_telemetry`
- `09_ml_artifacts`
- `10_large_mixed_binary`

Resemblance-hostile:

- `01_shifted_versions`
- `02_false_neighbors`
- `03_boundary_churn`
- `05_incompressible`

No other workload may be silently substituted into or removed from this gate after results are observed.

## Frozen EG08 mechanism

Unchanged from the Office pass:

- EG07 representation/geometry/recovery first;
- hot inverse-view roots identified only from authenticated reconstruction recipes and left unchanged;
- other physical packs use fixed effort ladder `3,6,12,19` starting from their current level-1/raw storage choice;
- retain best-so-far;
- continue after improvement or tie;
- stop at first strictly worse rung;
- no path, extension, workload identity, file type or corpus-derived byte threshold.

## Hypothesis H-EG08-ELIGIBLE9

Selective physical effort generalizes across the parent representation's valid domain as a zero-byte-regression encoder-side improvement while preserving reader/recovery geometry. Its current post-build implementation may reveal exported CPU/RSS debt; that debt must remain visible.

## Pass contract

`EG08_ELIGIBLE9_TRANSFER_PASSES` requires:

1. 9/9 fresh-process EG07 and EG08 builds complete;
2. 9/9 EG08 strong verification and deliberate-primary-corruption tail recovery pass;
3. 9/9 preserve EG07 member count, maximum decode unit and maximum member amplification exactly;
4. zero stored-byte regressions versus same-run EG07;
5. at least **two non-Office surfaces** achieve strict stored-byte wins, preventing Office-only credit;
6. Analytics is a strict stored-byte win versus EG07;
7. every workload gaining `<4 KiB` stays at `<=1.50x` EG07 creation CPU.

The low-yield CPU rule is an adversarial implementation-cost gate, not a product selector threshold. Failure there does not falsify the compression mechanism; it blocks the current post-build implementation until a cheap pre-gate or fused writer removes wasted work.

Peak RSS is reported per workload without an arbitrary synthetic threshold. Any material increase remains explicit promotion debt.

## Analytics mature comparator

Analytics additionally executes the exact frozen Genesis-v0.29 surface from `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` / `experiments/entropygraph_v029_residual_strict.py` with fail-closed source provenance. EG08 must remain at least `10x` faster in fresh-process CPU. Beating v0.29 bytes would be valuable but is not required for this transfer pass.

## Preservation

No locality ceiling, recovery/integrity semantics, version, format revision, release state, Genesis score or ONE evidence changes. The six EG07-ineligible surfaces remain preserved negative coverage evidence and are not relabeled.

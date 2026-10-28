# v0.30 EG08 eligible-nine transfer result — 2026-09-13

Status: **research evidence; promotion blocked only by exported creation economics**

Exact measured head: `32d587ac8ba688cf2caafd7e96718786a9cebc16`

Hosted run: `34763279430`

Receipt artifact: `10319478507`

Artifact digest: `sha256:b94c8a9a92b4dce82a7a5fc56fe20d12f126ceb1cebf8bde81c403759b532d95`

Scientific verdict: `EG08_ELIGIBLE9_TRANSFER_BLOCKED`

Exact failed condition: `low_yield_cpu_export_cost_ok`

## Preregistered transfer surface

The nine workloads were frozen before EG08 evidence was observed, from the EG07 locality-valid transfer map:

Neutral/current15:

- `02_office_workspace`
- `04_analytics_and_database`
- `05_logs_and_telemetry`
- `09_ml_artifacts`
- `10_large_mixed_binary`

Hostile:

- `01_shifted_versions`
- `02_false_neighbors`
- `03_boundary_churn`
- `05_incompressible`

## Result

The strict rerun used the strengthened v2 referee, which explicitly requires current-checkout module provenance and the strong-verification result in addition to the previously required recovery/locality/economic gates.

Across the nine preselected surfaces:

- EG08 saved **1,736,562 B** relative to EG07 in aggregate;
- it produced **7 strict wins outside Office**;
- the worst observed creation-CPU ratio versus EG07 was **10.352350213657903x**;
- the only failed preregistered condition was `low_yield_cpu_export_cost_ok`.

Therefore every other preregistered condition passed, including the exact nine-workload surface, current-source sealing, strong verification, zero stored-byte regressions, unchanged locality geometry, tail recovery, the non-Office generalization requirement, the Analytics strict byte win and the frozen-v0.29 Analytics speed requirement.

## Interpretation

EG08's mechanism generalizes in density beyond Office and survives the integrity/recovery/locality transfer. It is **not** yet a product/frontier promotion because its present research implementation performs EG07 first and then decompresses/recompresses physical packs through the fixed effort ladder. On low-yield surfaces that exported creation work can overwhelm the small byte saving.

This is a mechanism/implementation separation, not permission to weaken the gate. The next Builder must attack redundant creation work while preserving the same EG08 selected bytes/geometry or earn any changed representation through a new referee. Appropriate directions include fusing effort selection into first-pass physical creation, cheap opportunity gating, branch-and-bound and reuse of already-computed candidate work. No corpus/path/file-type threshold may be introduced to make the transfer green.

## Additional hostile review

Equal EG07/EG08 locality geometry proves that physical decode-unit raw sizes and amplification did not increase, but it does not prove that higher-effort Zstd frames preserve extraction/verification CPU, wall time or reader RSS. That exported reader cost is separately preregistered in `docs/V030_EG08_READ_COST_MISSION_LOCK_2026-09-13.md` and must be adjudicated before promotion.

## Score custody

This result does not alter the frozen Genesis scores, the existing composed-R4 score, the v0.29 release identity, the 8x locality law, or ONE's preserved secondary status. It is transfer evidence for one v0.30 research mechanism only.

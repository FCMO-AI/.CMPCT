# v0.30 EG07 transfer eligibility result — 2026-09-13

Status: **baseline-domain evidence; no EG08 promotion credit**

Exact measured head: `478efb65a328f24ff4632272dfb31d04784beca5`
Hosted run: `34762808445`
Receipt artifact: `10318888705`
Artifact digest: `sha256:5fc4ac8a3fb945fd6bba17563e824a1f7018e99610c8da6025a3ac3f559b09c9`

## Result

The preregistered EG07-only map classified **9/15** deterministic surfaces as product-valid under the existing frozen locality/decode contract. EG08 results were not consulted when assigning eligibility.

### ELIGIBLE

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

### INELIGIBLE_BASELINE

- Developer — EG07 exceeds frozen locality/decode limits.
- Media — EG07 exceeds frozen locality/decode limits.
- Incremental Backups — EG07 changes canonical filesystem semantics and correctly rejects itself.
- Neutral incompressible/encrypted-like — EG07 exceeds frozen locality/decode limits.
- Tiny Files — EG07 exceeds frozen locality/decode limits.
- Deflate-family hostile — EG07 exceeds frozen locality/decode limits.

These are negative evidence about **EG07 coverage**, not adaptive-effort failures. The locality ceiling is not widened to manufacture transfer coverage.

## Consequence for EG08 review

Generalization claims for EG08 must be restricted to the nine pre-mapped EG07-valid surfaces. The failed neutral10 and first hostile5 transfers are harness/domain failures where the unchanged parent representation is outside its own admitted product envelope; they receive no product-loss interpretation.

For adaptive-effort behavior on the six ineligible surfaces, use a fixed-pack synthetic/isolated referee that tests the encoder policy independently of EG07 geometry, or first rehabilitate the parent representation under the same safety/locality contract. Do not silently swap representations after seeing EG08 results.

## Preservation

No representation, locality limit, version, release state, Genesis score or ONE evidence changed. `research/cmpct1` remains untouched.

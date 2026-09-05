# ONE-G0.2 growable emitter boundary diagnostic — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Frozen authority: `docs/one/evidence/ONE_G02_GROWABLE_EMITTER_BOUNDARY_DIAGNOSTIC_PREREG_2026-09-05.md`

## Exact CI receipt

- branch source: `48c720a72137672b30a7e5242ae24d407c12ec65`
- pull-request merge test SHA / benchmark `EVIDENCE_HEAD`: `433937e49c08106210e78957e0ce056f4f6af19a`
- workflow run: `33992721864`
- job: `101377693859` (`growable-emitter-boundary-diagnostic`)
- conclusion: **success**
- artifact: `9977127674`
- artifact ZIP SHA-256: `eb25fb1eb7185bc0e02e6cb1a0a31ee4696fd7ac048b8ce98e36cc735f77bfc4`
- ONE semantic/hostile tests: **93 passed**
- frozen decision: **`classify_parent_outlier_nonrepeatable`**

## Result

The diagnostic swept the exact-shift and literal-control shapes at 13 target sizes from 96 KiB through 320 KiB, including several points immediately below and above 256 KiB, with 101 alternating paired A/B-B/A rounds per row. It also isolated the dominant blob-append operation.

Frozen decision fields:

- `all_shift_full_rows_le_1_03 = true`;
- `full_slow_sizes_ge_1_20 = []`;
- `blob_slow_sizes_ge_1_20 = []`;
- decision = `classify_parent_outlier_nonrepeatable`.

The exact 256 KiB shift row that had lost catastrophically in the parent gate measured here:

- baseline canonical emission: **63,008 ns**;
- growable-direct emission: **34,494 ns**;
- candidate / baseline: **0.547454x**;
- direct blob append / baseline helper-style blob append: **0.524713x**.

Neighboring exact-shift rows were likewise ordinary wins: 253,952 B **0.557756x**, 258,048 B **0.601153x**, 266,240 B **0.583268x**, 270,336 B **0.543562x**. No neighboring slowdown appeared and the isolated blob stage stayed roughly in the 0.50–0.59x range across the sweep.

## Causal interpretation

The frozen H1 claim is falsified: there is no evidence here for a reproducible `bytearray` growth/reallocation cliff around 256 KiB. The original parent-gate 256 KiB loss cannot be attributed to a stable size boundary.

The result instead authorizes exactly one thing under the preregistration: an unchanged repeatability run of the original parent gate. It does **not** retroactively turn the failed parent gate green and does not authorize a size threshold or workload dispatch.

The subsequent unchanged parent-gate rerun is recorded separately. If that mixed-envelope run again exhibits an isolated 256 KiB loss while this dense same-source size sweep remains fast, the remaining owner is execution-context / allocator-history / runner interaction or timing instability rather than a simple wire-size law.

## Claim boundary

Python runtime diagnostic only. No ONE representation, product writer path, stored bytes, reader semantics, integrity/recovery contract, format revision or v0.29/v0.30 comparison authority changes.
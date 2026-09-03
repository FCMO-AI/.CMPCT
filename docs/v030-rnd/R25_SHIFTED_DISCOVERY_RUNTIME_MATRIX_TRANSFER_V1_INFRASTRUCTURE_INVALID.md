# r25 position-independent discovery source — runtime-matrix transfer v1 infrastructure-invalid result

Status: **INFRASTRUCTURE_INVALID / ZERO SCIENTIFIC, PRODUCT OR RELEASE CREDIT**

Frozen parent preregistration: `R25_SHIFTED_DISCOVERY_RUNTIME_MATRIX_TRANSFER_V1_PREREG.md`.

Exact source: `227c23a40b8ad7820fdfc982c0eac3438e7f3f49`  
Workflow run: `33807253413`  
Substantive job: `100821201708`

## Failure

The substantive two-pair transfer instrument executed for roughly ten minutes but terminated before emitting its frozen JSON receipt. The failure was:

```text
ZeroDivisionError: float division by zero
... "delta_wall_ratio": inherited_delta / baseline_delta
```

At least one measured target legitimately produced a zero `baseline_delta` timing value. The frozen validity grammar already requires positive finite child/delta timings, so such a row must make the experiment `INVALID`; the instrument must not crash while trying to serialize the invalid condition.

Because no complete receipt was emitted, no partial timing, byte identity, call count or apparent workload result from this run receives transfer-decision credit.

## Custody decision

Do not edit or reinterpret the v1 frozen instrument in place. A superseding v2 freeze may repair only result serialization/invalid-state handling:

- preserve the same three targets;
- preserve the same two alternating paired repetitions;
- preserve the same single ablation;
- preserve the v1 validity and terminal-decision grammar;
- when a denominator required only for a reported supporting ratio is non-positive/non-finite, serialize that ratio as `null` and allow the already-frozen validity checks to drive terminal `INVALID` rather than raising;
- make no product, archive, comparator, threshold, locality, integrity, recovery or release change.

This run is evidence about instrument robustness only, not about whether the discovery source transfers.

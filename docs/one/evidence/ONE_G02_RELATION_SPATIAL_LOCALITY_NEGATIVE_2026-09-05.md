# ONE-G0.2 — Relation spatial-locality A/B: stream separation is not the dominant residual

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable causal negative; physical source/target separation retired as dominant residual explanation  
**Result-bearing source:** `fca88557ea97aaf9ccc978b36ae1d23ea77c4dd1`

## Mission Lock

The arbitrary-relation transfer remained above its frozen cost ceiling after pointer rebasing, and the direct-pointer A/B showed that carrier/offset ABI work was real but not the dominant residual. This already-frozen discriminator held the direct-pointer function, relation bytes, cases, relation lengths and semantics fixed while changing only physical placement: adjacent source/target bytes versus copies separated by hundreds of KiB.

The preregistered causal gate required far placement to be at least **5% slower on every frozen 32/64 KiB row** before cache/TLB/prefetch effects could be treated as the dominant remaining owner. Failure retires that explanation rather than tuning the threshold after result.

## Exact-head receipt

- workflow: `33962453827`
- job: `101296582171`
- artifact: `9968357463`
- artifact zip SHA-256: `c2a8750fccf57b3de11d0bff01b57023b51abf2bb1da7625776799333dce6e6b`
- `tests/one`: **76 passed**
- decision: `stream_separation_not_dominant_residual_owner`
- all result structs: exact

The job exits non-zero by design when the dominant-owner hypothesis is falsified; the artifact was retained under `if: always()` and is the result-bearing evidence.

## Result

Observed far-placement slowdown fractions were tiny and mixed in sign:

| relation | case | adjacent ns | far ns | far slowdown |
|---:|---|---:|---:|---:|
| 32 KiB | shift +1 | 2073.0 | 2072.5 | -0.024% |
| 32 KiB | quarter-damaged +1 | 2105.0 | 2098.5 | -0.309% |
| 32 KiB | every96 positive | 2136.0 | 2127.0 | -0.421% |
| 32 KiB | every32 false control | 2103.5 | 2104.5 | +0.048% |
| 32 KiB | independent random | 2038.5 | 2037.0 | -0.074% |
| 64 KiB | shift +1 | 3424.0 | 3419.0 | -0.146% |
| 64 KiB | quarter-damaged +1 | 3227.0 | 3228.0 | +0.031% |
| 64 KiB | every96 positive | 3453.5 | 3452.0 | -0.043% |
| 64 KiB | every32 false control | 3453.0 | 3452.0 | -0.029% |
| 64 KiB | independent random | 4461.5 | 4467.0 | +0.123% |

The entire observed envelope is approximately **-0.42% to +0.12%**, two orders of magnitude smaller than the 5% dominant-owner gate.

## Causal interpretation

Physical stream separation does not explain the remaining generic-relation cost gap. The next discriminator must therefore inspect **code shape / benchmark measurement shape** while keeping relation semantics unchanged. In particular, the prior transfer compared independently timed medians, whereas the successful direct-pointer attribution used paired ABBA ordering. A paired direct-pointer-vs-half-layout A/B is the lowest-sufficient next test: if the generic direct kernel satisfies the existing <=1.10x transfer ceiling under paired timing, the earlier residual is primarily a measurement/thermal-frequency artifact rather than a representation cost. If it still loses, the residual survives as generated-code/loop-shape debt and should be attacked there rather than through locality or API heuristics.

## Claim boundary

Writer-side causal compute attribution only. No ONE representation, reader-visible operation, stored-byte result, product-speed claim, v0.29/v0.30 comparison or release authority changes.

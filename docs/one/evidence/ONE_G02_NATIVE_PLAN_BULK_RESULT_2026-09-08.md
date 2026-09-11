# ONE-G0.2 Native Plan Bulk — exact result

Decision: **ADVANCE_NATIVE_PLAN_BULK**

## Provenance

- branch: `research/cmpct1`
- exact result source: `7f8405c8cce517e4fe3b15426fb97d1df469ab03`
- Actions run: `34290378854`
- job: `102275368807`
- artifact: `10081123391`
- artifact digest: `sha256:6fc12056c577464afae68e4bff42c72783f3d5f6eb55f56890445164c1df581d`
- repetitions: 9 paired, alternating arm order
- exact matrix: 18/18
- semantic/work-accounting truth: green
- semantic + decision-law tests: green

The earlier source `8d7a2b6315b861db0faa845992f543f0e8b96257` is not performance authority; hostile review added an explicit unknown-operation fail-closed check before the exact evidence lane was established. Scientific thresholds did not move.

## Frozen decision law

Advance required every XOR/add8 row at 64 KiB, 256 KiB and 1 MiB to be <=0.35x the generic prepared-plan wall **and** CPU medians, while all twelve non-arithmetic rows remained <=1.05x. Semantic/work disagreement or an incomplete/duplicate matrix invalidated.

Result: **ADVANCE_NATIVE_PLAN_BULK**.

## Exact row summary

| size | family | native/generic wall | native/generic CPU |
|---:|---|---:|---:|
| 64 KiB | terminal_mix | 1.0162x | 1.0173x |
| 64 KiB | repeat | 0.9897x | 0.9898x |
| 64 KiB | slice_concat | 1.0002x | 0.9994x |
| 64 KiB | xor2 | **0.01054x** | **0.01055x** |
| 64 KiB | add8_3 | **0.004151x** | **0.004152x** |
| 64 KiB | shared_basis | 0.9991x | 0.9986x |
| 256 KiB | terminal_mix | 1.0208x | 1.0231x |
| 256 KiB | repeat | 0.9772x | 0.9773x |
| 256 KiB | slice_concat | 1.0073x | 1.0073x |
| 256 KiB | xor2 | **0.007798x** | **0.007802x** |
| 256 KiB | add8_3 | **0.003635x** | **0.003638x** |
| 256 KiB | shared_basis | 1.0060x | 1.0059x |
| 1 MiB | terminal_mix | 0.9975x | 0.9977x |
| 1 MiB | repeat | 0.9989x | 0.9989x |
| 1 MiB | slice_concat | 1.0107x | 1.0107x |
| 1 MiB | xor2 | **0.005959x** | **0.005960x** |
| 1 MiB | add8_3 | **0.002946x** | **0.002947x** |
| 1 MiB | shared_basis | 0.9960x | 0.9958x |

At 1 MiB, generic prepared XOR required ~173.69 ms wall and native bulk ~1.035 ms. Generic prepared three-parent add8 required ~499.36 ms and native bulk ~1.471 ms. Thus the experiment removes roughly 99.4% and 99.7% respectively of the hosted Python arithmetic time while preserving the exact ONE Program, work accounting and root authentication.

## Causal interpretation

`ADVANCE_GENERIC_EXECUTION_PLAN` separated the reader into a reusable control plane; this result shows the remaining arithmetic owner belongs in a bulk data plane. The strongest architecture supported by current evidence is therefore:

**validated generic ONE execution plan + bounded bulk kernels for existing byte-heavy Law operations.**

This is not a hidden codec zoo. XOR/add8 were already part of the minimal ONE grammar; no reader-visible operation or representation changed. The kernel only changes how those existing operations execute.

Non-arithmetic rows are the control: all remain inside 1.0231x, with the 1 MiB matrix inside 1.0107x. The enormous arithmetic gain therefore is not purchased by broad reader regressions.

## Claim boundary / surviving objections

This is hosted Linux/CPython/C11 hot-replay evidence. `ctypes.c_char_p` is research machinery, not a portability decision. Native-library build/startup is intentionally outside replay timing because a built reader would ship compiled; no startup claim is made.

Python slice materialization remains charged. This result therefore does not establish optimal memory traffic, direct operand views, selective-range performance, RSS improvement, or a canonical native ABI. It also does not move stored density by itself.

The strongest remaining reader-side opportunity is to feed native kernels direct bounded views/offsets from a prepared reconstruction plan rather than materialized Python slices, but that is lower priority than returning writer research to automatic Law discovery now that the existing general grammar has a credible execution architecture.

## Decision / next action

Advance the **generic prepared control plane + native bulk data plane** principle. Preserve this as an implementation architecture for existing ONE operations. Shift primary research budget back to automatic Law discovery: fused observation, sparse opportunity gating, and compilation of useful predictive structure into the same six-op Law + Surprise grammar. Reader-side view/offset fusion remains a separately preregistered optimization, not a prerequisite for writer discovery.
# ONE-G0.2 terminal Law root-sink result — 2026-09-08

Status: **HOLD_TERMINAL_LAW_ROOT_SINK** on corrected exact source `e5f772af91d1988f76a6af641daac9facbe8287c`.

## Exact evidence authority

- workflow run: `34271793586`
- job: `102214901621`
- artifact: `10074177713`
- artifact ZIP SHA-256: `a8c317ca47590b3b694d082b556126e73cd0b6639f0af3b536d820688b08f25e`
- semantic/decision-law tests: **15 passed**
- benchmark verdict: `HOLD_TERMINAL_LAW_ROOT_SINK`

## What survived falsification

The corrected memoryview-based root sink preserves exact reconstruction and root commitments on the full 15-row matrix. The useful run Law also preserves its density result: at 1 MiB, `long_runs` is `0.501019x` literal wire and `structured` is `0.875018x`.

Modeled fused memory traffic moves in the intended direction. At 1 MiB, `long_runs` is `0.900x` literal-control traffic and `structured` is `0.975x`; peak temporary bytes remain `1.000x`. Thus the extra child-materialization pass is not required by the stored ONE graph.

## Why the candidate holds

Timing falsifies the scalar execution shape. The 1 MiB `long_runs` row contains 220 qualifying Fill runs and measures:

- literal control wall: `1,645,350 ns`
- scalar fused candidate wall: `2,625,725 ns` (`1.595846x`)
- literal control CPU: `1,646,826 ns`
- scalar fused candidate CPU: `2,627,118 ns` (`1.595261x`)

The same pattern exists at smaller scales: `1.622395x` wall for 14 Fill runs at 64 KiB and `1.628582x` for 55 Fill runs at 256 KiB. Structured has only one Fill and is essentially neutral by 1 MiB (`1.002650x` wall, `1.000383x` CPU). Controls with no useful Fill are also essentially neutral at 1 MiB.

This is mechanism-level evidence that the Law and root-sink traffic reduction are viable while repeated Python-to-ctypes Fill dispatch is not. It does **not** yet prove that dispatch alone owns the entire regression; the next falsifier must batch the same Fill schedule through one native call while charging schedule construction.

## Claim boundary

No reader-visible opcode, stored grammar, integrity rule, selective-read contract, comparator, or Genesis authority changes. This result concerns full-root execution of the existing terminal Surprise/Fill/Concat graph only.

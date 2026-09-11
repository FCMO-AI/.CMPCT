# ONE-G0.2 native terminal Fill batching preregistration — 2026-09-08

## Mission lock / falsifiable hypothesis

Corrected root-sink evidence shows the existing terminal Law graph reduces long-run wire to ~0.501x and fused memory traffic to 0.900x, yet the 1 MiB row with 220 Fill spans is ~1.596x literal-control time. Hypothesis: repeated Python→ctypes `memset` dispatch, rather than the Law or the eliminated materialization pass, is the dominant avoidable regression.

Disproof: batch exactly the same Fill spans through one native call per root **while charging Python schedule construction**. If this does not make every row <=1.05x literal control on both wall and CPU and make every long-run row <=0.75x the scalar fused candidate, dispatch alone is not sufficient to rehabilitate the execution shape.

## Frozen matrix and arms

Fresh subprocess per row: 64 KiB, 256 KiB, 1 MiB × `structured`, `compressed_like`, `long_runs`, `random`, `near_repeats`. Each row uses 21 measured repetitions after equal warmup, with rotating three-arm order:

1. literal Program + scalar fused terminal reader;
2. same run-Fill Program + scalar fused terminal reader;
3. same run-Fill Program + native-batched Fill reader.

Program construction, observation, compilation and wire round-trip occur before reader timing for all arms. Native library compilation is warmup and therefore outside measured steady-state reader calls. Schedule construction is inside each bulk reader call and remains charged.

## Frozen gates

- exact complete 15-row matrix and semantic equality are mandatory;
- candidate wire may never exceed literal control;
- 1 MiB `long_runs` wire <=0.55x and `structured` <=0.90x;
- bulk modeled traffic and peak temporary memory <=1.05x literal control on every row;
- bulk wall and CPU <=1.05x literal control on every row;
- on every `long_runs` row, bulk wall and CPU <=0.75x the scalar fused run-Fill reader.

Any semantic failure invalidates. Missing/duplicate cells invalidate. Thresholds are frozen before hosted results.

## Claim boundary

A green result proves only that one native Fill schedule can remove enough scalar dispatch overhead to make this bounded full-root execution strategy viable. It does not create a new opcode, change stored ONE bytes, prove selective-range behavior, choose a portability backend, or move Genesis comparator authority.

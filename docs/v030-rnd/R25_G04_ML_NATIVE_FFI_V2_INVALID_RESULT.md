# R25 G0-G4 ML native in-process FFI v2 — invalid instrument result

Status: **CANDIDATE_INVALID — zero scientific decision credit**

## Immutable execution receipt

- workflow: `.github/workflows/v030-g04-ml-native-ffi-reader-v2.yml`
- run: `33761156363`
- substantive job: `100667522734`
- source commit: `0036b75be2eba9b94789fff489b5a3f392df2e9d`
- intended target: `neutral_hostile_v1/09_ml_artifacts`
- intended rounds: 5 alternating Python/native pairs
- frozen bands: >=20% median verify improvement **and** >=20% median extract improvement
- release credit: none

The workflow itself was valid and exact-SHA custody was green, but candidate construction failed before compilation or any A/B sample. The exact failure was:

`error: corrupt patch at benchmarks/patches/v030_g04_operation_record_cache.patch:48`

The v2 preregistration had assumed that existing research patch was valid current-head transport. It was not. The job skipped compilation, correctness, and the scientific A/B; no result artifact existed. CI topology self-check did pass, confirming the exact-SHA concurrency repair independently.

## Causal interpretation

This remains a D0 candidate-construction failure. It is not evidence for or against shared physical-record reuse. The scientific worldview is still untested.

## Preservation / reopening predicate

The v2 preregistration, workflow and run are immutable after this execution. A superseding v3 may replace only candidate-construction transport with a fail-closed exact-source mutator. It must preserve the same target, comparator, five alternating pairs, in-process FFI timing boundary, archive/grammar/selector identity, integrity and corruption rejection, caller output-budget preflight, 8x locality, 8 MiB decode-unit law, memory law, and the unchanged 20% verify + 20% extract decision bands.

# ONE-G0.2 second-stage relation kernel A/B preregistration — 2026-09-10

## Mission lock

Measure the actual CPU/wall consequence of the hosted-green 15-midpoint rejection oracle at the exact relation-check boundary used by the Python general writer, before attempting full writer integration.

This is a causal kernel experiment. It starts after a candidate has already passed the existing primary 16-point sampler and economic admission. No Genesis input, archive serialization, authentication or reader path is involved.

## Arms

Baseline for ADD8/XOR: execute the existing complete `_all_add8` / `_all_xor` relation proof.

Candidate: inspect the frozen 15 second-stage midpoint positions. If any position disproves the nominated constant relation, reject immediately. Otherwise execute the same complete `_all_add8` / `_all_xor` proof.

The second stage is rejection-only and can never accept a Law.

## Frozen matrix

Lengths: `256, 4096, 16384, 65536, 262144` bytes.

Relations: ADD8(+37), XOR(0xA5).

Kinds:
- `true`: exact relation;
- `stage2_collision_first`: one poison byte on the **first** second-stage midpoint; this measures the best early-reject geometry for the candidate;
- `stage2_collision_last`: one poison byte on the **last** second-stage midpoint; this prevents the result from depending on an artificially favorable first-probe mismatch;
- `dual_collision_early`: one poison byte at the first position outside primary + second-stage positions; both sparse stages miss it while the baseline exact proof may reject very early, deliberately exposing worst-case second-stage overhead.

Input generation must be deterministic and independent of Genesis. The benchmark must independently assert that every hostile kind passes the existing primary 16-point sampler and that the true kind is exact.

This hostile-geometry amendment was committed **before any isolated v2 hosted result was adjudicated**. The earlier unisolated v1 timing schema is invalid for promotion because it recomputed primary-sampler work inside the timed arms.

## Timing method

- CPython hosted runner;
- primary positions and nominated ADD8 delta/XOR mask are computed before timing and shared by both arms;
- neither timed arm may call `_sample_positions` or re-nominate the relation;
- alternate baseline/candidate execution order by repetition;
- warm both arms before timed repetitions;
- `REPETITIONS = 101` per row;
- report median process CPU and wall nanoseconds;
- report candidate/baseline ratios per row;
- preserve modeled observed-byte accounting from the prior oracle as explanatory data only.

The benchmark must consume the boolean results so no arm can be optimized away by benchmark code.

## Gates

H1 correctness:
- baseline and candidate return identical truth values on every row;
- true rows return true;
- all hostile rows return false;
- full exact proof remains the only positive authority.

H2 hostile benefit:
- for every `stage2_collision_first` **and** `stage2_collision_last` row at >=4096 B, median candidate CPU ratio <=0.50 OR candidate wall ratio <=0.50;
- no stage-2-collision row may exceed baseline by repository timing noise: +5% relative or +0.003 s absolute.

H3 survivor debt:
- true and `dual_collision_early` rows preserve their expected extra sparse work;
- at 4096 B+ their median CPU and wall ratios must each remain <=1.20, otherwise fixed midpoint reads are too expensive for this implementation shape.

H4 broad kernel economics:
- aggregate median CPU ratio over all >=4096 B rows <=1.00;
- aggregate median wall ratio over all >=4096 B rows <=1.00.

H5 geometry sensitivity:
- preserve first-vs-last stage-2 collision ratios separately;
- the decision may not average away a failure of `stage2_collision_last` using the easier first-collision rows;
- preserve `dual_collision_early` individually; its overhead is an explicit adversarial debt rather than noise.

## Decision

- H1 failure: `RETIRE_SECOND_STAGE_RELATION_KERNEL`.
- H1 passes but H2/H3/H4/H5 fails: `HOLD_SECOND_STAGE_RELATION_KERNEL`.
- all pass: `ADVANCE_SECOND_STAGE_RELATION_KERNEL_TO_WRITER_AB`.

An ADVANCE only permits the already-preregistered full writer A/B. It does not enable the mechanism by default.

## Hostile interpretation

`dual_collision_early` rows are intentionally capable of making the baseline exact proof fail almost immediately while the candidate pays sparse-stage overhead first. This is the implementation shape's real downside and must remain visible.

If the aggregate win depends on hiding that class, the experiment fails. If Python indexing is expensive even when modeled bytes improve sharply, preserve the negative and prefer reuse of fused/native observation state rather than tuning sample count post hoc.

If first-collision rows win but last-collision rows fail H2, the sparse stage is not broadly justified: its apparent benefit came from favorable probe ordering.

## Genesis separation

All result artifacts must set Genesis execution/comparison/scoring/winner flags false.

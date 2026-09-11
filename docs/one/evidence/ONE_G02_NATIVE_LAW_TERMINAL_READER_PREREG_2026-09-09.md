# ONE-G0.2 Native Law Terminal Reader — preregistration

Date: 2026-09-09
Experimental version: ONE-G0.2
Status: FROZEN BEFORE HOSTED TIMING

## Mission lock

Test whether ordinary ONE terminal Law cones can be lowered into one bounded native execution schedule without adding any stored opcode or reader discovery. The first causal target is the modern relation topology already emitted by the writer: Surprise + Fill + add8/xor, optionally joined by Concat and literal crack spans.

This is an evaluator execution experiment, not a format experiment. Unsupported topology must fail closed so the incumbent VM/range reader remains authoritative.

## Referee hypothesis

For eligible whole-root relation Programs, a generic native COPY/FILL/ADD8_CONST/XOR_CONST execution plan will preserve exact ONE semantics and the logical resource advantage of terminal fusion while removing the Python byte-loop penalty that made the earlier generic fusion reader slower in wall/CPU.

## Disproof conditions

The result is HOLD or INVALID if any of the following occurs:

1. Any output byte, root length, or SHA-256 root differs from the reference evaluator.
2. Stored Program/wire semantics are changed to obtain the result.
3. Unsupported or partial-root topology is silently accepted instead of failing closed.
4. Native modeled work exceeds the Program's declared work limit.
5. Median hot native CPU on eligible Law rows exceeds 0.75x reference VM CPU, or any eligible row exceeds 1.00x.
6. Median hot native CPU on terminal control rows exceeds 1.10x reference VM CPU, or any control exceeds 1.25x.
7. Median native modeled memory traffic on eligible rows exceeds 0.75x reference VM runtime work, or native peak temporary bytes exceed the requested root length.
8. Preparation cost is hidden. Compile/preflight time, packed source-plan bytes, command count, and hot replay time must be reported separately.

A timing miss does not authorize threshold changes. It identifies the next cost owner.

## Frozen matrix

Scales: 32 KiB, 128 KiB, 512 KiB per version/root.

Eligible Law families:
- add8 exact relation
- xor exact relation
- add8 relation with one explicit crack span represented by Concat
- xor relation with one explicit crack span represented by Concat

Terminal controls:
- explicit Surprise root
- Fill root
- Surprise/Fill Concat root

Hostile semantic controls:
- partial authenticated root range: reference evaluator must succeed, native whole-root compiler must reject
- xor/add8 with two nonconstant Surprise operands: reference evaluator must succeed, constant-Law native compiler must reject
- malformed/over-budget Programs continue to be rejected by ordinary validate/preflight before native execution

Nine alternating timing rounds are used after one untimed warm-up. CPU and wall medians are retained. Program preparation is timed independently from hot execution and is never folded out of the report.

## Accounting

For each row retain at minimum:
- exact semantic parity
- baseline VM CPU/wall and EvaluationStats
- native preparation CPU/wall
- native hot CPU/wall
- native/reference CPU and wall ratios
- reference materialized bytes and work bytes
- native modeled memory traffic and peak temporary bytes
- packed source-plan bytes and command count
- root bytes and throughput

No selective-read victory may be claimed from this experiment because the native compiler intentionally accepts complete authenticated roots only. Partial-root support remains a separate integration requirement and must continue through the incumbent range evaluator until explicitly proven.

## Promotion meaning

ADVANCE means the existing generic ONE representation can execute modern terminal relation cones through bounded native bulk operations efficiently enough to justify integrating the execution strategy into the canonical reader surface. It does not mean all ONE operations or selective ranges are natively covered, and it does not authorize relation-specific stored semantics.

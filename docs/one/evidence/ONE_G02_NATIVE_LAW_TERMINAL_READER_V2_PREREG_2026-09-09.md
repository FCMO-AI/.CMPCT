# ONE-G0.2 Native Law Terminal Reader V2 — preregistration

Date: 2026-09-09
Experimental version: ONE-G0.2
Status: FROZEN BEFORE HOSTED V2 TIMING

## Mission lock

Rehabilitate the V1 HOLD without weakening its gates. V1 proved a very large CPU win on ordinary add8/xor Law cones but failed because it (a) routed no-Law controls through the candidate and (b) wrote into a mutable root sink and then copied the entire root again to freeze it.

V2 changes only those cost mechanisms:

1. a static graph-level eligibility check (`add8`/`xor` node present) routes no-Law Programs to the incumbent evaluator;
2. eligible roots execute directly into one newly allocated final immutable Python bytes object, which is not exposed until native writes and SHA-256 verification finish.

No stored ONE operation, wire byte, root identity, Program resource rule, or reader discovery changes.

## Frozen gates

Retain V1 thresholds exactly:

- semantic parity: exact on every row;
- median eligible native/reference CPU <= **0.75x**;
- every eligible native/reference CPU <= **1.00x**;
- median control candidate/reference CPU <= **1.10x**;
- every control candidate/reference CPU <= **1.25x**;
- median eligible native modeled traffic/reference VM work <= **0.75x**;
- native peak temporary bytes <= one requested root length.

Preparation time, packed source-plan bytes, command count, and static eligibility-check cost remain visible. Do not fold preparation into hot replay and do not hide it.

## Frozen matrix

Exactly the V1 21 performance rows:

- sizes: 32 KiB, 128 KiB, 512 KiB per version/root;
- eligible: add8, xor, add8+one explicit crack, xor+one explicit crack;
- controls: literal Surprise, Fill, Surprise/Fill Concat.

Retain the V1 hostile semantics:

- partial authenticated root range succeeds through incumbent reference but native whole-root compiler rejects;
- nonconstant two-Surprise xor/add8 shape succeeds through reference but constant-Law compiler rejects;
- ordinary validate/preflight owns malformed and over-budget rejection.

Nine alternating hot rounds after warm-up. Exact same deterministic case generator as V1.

## Direct-final safety invariant

The CPython bytes object is allocated at final size, populated through its private pointer before the object leaves the execution function, then SHA-256 authenticated before return. Any native schedule error or digest mismatch aborts; no partially populated object is returned.

This is the reader analogue of direct final-buffer emission: remove an intermediate copy, not an integrity check.

## Promotion meaning

ADVANCE means generic native terminal Law execution has cleared the V1 whole-root CPU/control/traffic envelope and can become the preferred execution strategy for the eligible topology behind fail-closed incumbent fallback.

It does **not** grant selective-range authority. Authenticated partial-root/range reconstruction remains on the incumbent path until separately proven.

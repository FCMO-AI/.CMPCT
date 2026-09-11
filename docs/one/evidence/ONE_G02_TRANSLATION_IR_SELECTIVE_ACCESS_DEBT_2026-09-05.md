# ONE-G0.2 — generic translation IR selective-access debt

Date: 2026-09-05

## Mission Lock / Referee freeze

The automatic translation Law+Surprise result had already shown that sparse temporal/version edits compile into the existing generic ONE IR without adding a bespoke reader opcode. This activation tested a different claim: whether the current experimental wire + reference evaluator can serve a 4 KiB range from the edited root without materializing unrelated information.

This is a current-implementation falsifier, not a theoretical lower bound on ONE locality. The public experimental reader currently exposes whole-program decode plus whole-root evaluation, so the experiment charged that complete path. Promotion required median materialized amplification <=8x and median reconstruction-work amplification <=16x for both tested source sizes. The benchmark was frozen before result-bearing execution.

## Exact evidence

- source SHA: `bf12c96bc73632a5e5631cace27f15ea244bb60d`
- workflow run: `33948794239`
- result-bearing job: `101259569986`
- artifact: `9964148229`
- artifact ZIP SHA-256: `368f0b5847f25dc939f6363cdca66b29c54a9d92b87d69bfe72cda9010b64c9f`
- semantic boundary: **50/50 `tests/one` passed**
- rows: **64**
- requested range: **4,096 bytes**
- reconstruction exactness failures: **0**

### 65,536-byte sources

- median wire amplification: **16.0604x**
- median materialized amplification: **32.0024x**
- median reconstruction-work amplification: **112.0024x**
- maximum materialized amplification: **32.015625x**
- maximum reconstruction-work amplification: **112.015625x**

### 262,144-byte sources

- median wire amplification: **64.0625x**
- median materialized amplification: **128.0024x**
- median reconstruction-work amplification: **448.0024x**
- maximum materialized amplification: **128.015625x**
- maximum reconstruction-work amplification: **448.015625x**

## Decision

**Preserve the density result; open explicit selective-access debt.** The frozen access gate failed by a large margin at both sizes. This is not a threshold problem and the benchmark must not be tuned around the result.

## Causal interpretation

The generic representation itself is not falsified. The dominant current debt is architectural: `decode_program()` materializes the serialized program and the reference `evaluate()` materializes complete reachable node outputs and authenticates complete roots before the caller can slice the requested range. The amplification scales with source size, which is exactly the behavior a selective reader must avoid.

The next Builder should therefore separate three costs that the current public path conflates:

1. **reconstruction-cone work** — can generic Law operations evaluate only the requested output interval?
2. **wire access/index work** — can the reader find the required nodes/Surprise bytes without parsing/touching the whole program?
3. **integrity work** — can the requested interval retain hard authentication without a whole-root SHA-256 scan?

A cone-only evaluator may be useful diagnostic evidence, but it may not be promoted as a complete selective-read solution if it silently drops root authentication. Any integrity/index structure must remain generic ONE metadata rather than a temporal/version-specific reader mechanism.

## Hostile-review boundary

This result does **not** show that ONE inherently requires 32x–448x selective-read work. It shows that the current experimental whole-program wire + whole-root VM does. Conversely, the excellent incremental storage density of the translation Law does **not** excuse this access debt. The project must make both properties true under one reader model.

No v0.29/v0.30 comparator, product-speed, release, or canonical-format authority is created by this experiment.

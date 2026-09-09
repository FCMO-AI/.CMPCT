# ONE-G0.2 Single-Pass Relation Signatures — Result (2026-09-09)

## Decision

**HOLD_SINGLE_PASS_RELATION_SIGNATURES**

The exact-source fail-closed hosted falsifier preserved V4 semantics, wire, selection, accepted relation coverage, and halved positive relation-nomination source traffic, but failed the preregistered nomination-CPU rehabilitation gate. The retained signature array and seed-derivation scan cost more CPU than V4's second sparse source pass.

This is a negative result to preserve, not a reason to weaken V4 or its economic gates.

## Exact authority

- branch: `research/cmpct1`
- experimental version: `ONE-G0.2`
- source SHA: `7cca4719e1d97052370dece29794bada52b28767`
- workflow: `cmpct1-one-g02-single-pass-relation-signatures`
- run: `34350193707`
- job: `102461286933`
- artifact: `10103489887`
- artifact digest: `sha256:1bd7476789a00b26f7782eeba4ad49bde1d2d726594eddf0e801fbea0981caf1`

Exact checkout/frozen-law binding and inherited semantic adversaries passed. The falsifier returned HOLD and therefore the workflow correctly failed closed while still uploading the row-level artifact.

## Headline measurements

Across the frozen 27-row V4 matrix:

- median V5/V4 **nomination CPU**: **1.090952x**;
- worst V5/V4 nomination CPU: **1.186331x**;
- frozen nomination gates: median <= **0.60x**, every novel row <= **0.80x** — **FAIL**;
- median V5/V4 whole-writer novel CPU: **0.998730x**;
- worst V5/V4 whole-writer novel CPU: **1.005175x**;
- median V5/V4 control CPU: **1.030684x**;
- worst V5/V4 control CPU: **1.049426x**.

The candidate therefore remained basically whole-writer neutral because exact proof dominates positive CPU, but it did not justify the added signature state/scan on its own causal target.

## What did work

The source-traffic hypothesis was mechanically correct:

- V5 relation probe traffic: exactly **0.046875x combined input** on every row;
- V4 positive nomination traffic: **0.09375x**;
- therefore V5 removes the second positive source-probe pass entirely.

All rows remained semantically exact. V5 final canonical wire was byte-identical to V4, final selection matched, selected `(op,value)` matched on novel rows, accepted relation bytes matched, and proof bytes did not increase.

At 1 MiB combined input:

- exact add8/XOR remained **524,430 B** versus V4;
- sparse-crack add8/XOR remained **524,656 B**;
- exact relations retained **524,288 B** accepted coverage;
- sparse cracks retained **524,280 B** accepted coverage.

No control entered expensive exact relation proof.

## Why it held

V4's second sparse native pass reads only three byte pairs per block and directly appends matching offsets. V5 instead writes a 16-bit signature for every block, retains that array, then scans the array after selecting the global winner.

On this CPU/matrix, reducing sparse source traffic is cheaper than adding that memory write + retained-state + second in-memory scan. The result is useful because it falsifies a tempting but simplistic interpretation of `observe once`: **one source pass is not automatically more compute-efficient if it exports more intermediate state and memory traffic.**

This is directly relevant to ONE's marginal-information-yield law. Source bytes avoided are not free wins; memory writes and cache traffic also count.

## Strongest positive-path evidence

The 1 MiB rows remained dominated by exact proof, not nomination:

- add8 exact V5 proof CPU: about **46.0 ms**;
- XOR exact: about **41.85 ms**;
- sparse add8: about **45.94 ms**;
- sparse XOR: about **41.68 ms**.

That makes further signature bookkeeping optimization a lower-value target than accelerating the exact verifier while preserving its proof semantics.

## Stop condition

Do **not** promote the retained-signature design merely to achieve a single source pass. Do not tune its frozen CPU thresholds or add family-specific shortcuts.

Reopen this class only if a future already-required fused observation record can carry the relation signature at essentially zero incremental state/write cost, or if profiling on the integrated writer shows source-memory traffic—not proof CPU—is again dominant.

For the current research frontier, retain V4's sparse two-pass nomination and move effort to native/bulk exact proof.

## Campaign boundary

Frozen Genesis comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No v0.30 development is reactivated. This HOLD has no effect on the September 11 full Genesis comparator gate.

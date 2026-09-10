# ONE-G0.2 Crystallization marginal-cost model — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED BEFORE RESULT-BEARING EXECUTION**

## Mission lock

The hosted complete-wire geometry has shown that current generic Crystallization has stable economic crossovers on transfer data, but a measured crossover length is not itself a product rule. The research question is whether complete-wire admission can be explained and predicted by the marginal representation cost of the accepted Law versus the Surprise bytes it eliminates.

The model must not be a family-specific length table. It may use only information already available at the moment an encoder has exactly proved a nomination: relation kind, target length, constant/value representation, already-existing predictor/root state, and deterministic serialization-cost primitives. It may not inspect Genesis, benchmark identity, filename, workload class, or a learned corpus threshold.

## Frozen transfer matrix

Families:

1. exact reuse of an immediately preceding deterministic high-entropy file;
2. ADD8(+37) over an immediately preceding deterministic high-entropy Surprise source;
3. XOR(0xA5) over an immediately preceding deterministic high-entropy Surprise source;
4. Fill(`Q`).

Lengths, chosen to attack the observed transition and serialization/resource-boundary neighborhoods rather than only powers of two:

`2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 31, 32, 33, 63, 64, 65, 127, 128, 129, 255, 256, 257, 511, 512, 513, 1023, 1024, 1025, 4095, 4096, 4097, 16383, 16384, 16385`

The builder receives only the tree path. It receives no family label, expected relation, crossover, or admission hint.

## Arms and measurements

For each row, build the current generic ONE archive and same-input authenticated Surprise-only control exactly as in the geometry experiment. Preserve complete `len(wire)` bytes, signed actual delta, semantic/structural proof, deterministic wire, and reader ontology.

Independently compute a marginal-cost prediction from the candidate representation. The prediction must be based on representation facts rather than a fitted length cutoff. The first model under test is an affine local-cost hypothesis:

- Fill: replacing `n` Surprise payload bytes by one generic Fill root has a fixed local representation penalty `K_fill`, so predicted delta is `K_fill - n`;
- ADD8/XOR: replacing the target Surprise payload by one constant Fill node plus one binary Law node has fixed local penalty `K_binary`, so predicted delta is `K_binary - n` while retaining the existing predictor;
- exact reuse: reusing an existing root removes target Surprise payload and avoids creation of a target data node; its fixed local term is permitted to differ from Fill/binary Law but must be derived from representation accounting rather than a length table.

Constants used by the model must be derived from deterministic serialization/accounting primitives or from an explicitly isolated calibration construction that does not use any result row in this frozen matrix. No least-squares fit or per-family crossover tuning against the matrix is permitted.

## Falsifiable hypotheses

H1 — **sign safety**: the model has zero false admits across the frozen matrix. If predicted delta is <= 0, actual complete authenticated delta must also be <= 0.

H2 — **boundary fidelity**: the model remains sign-correct immediately around the tiny ADD8/XOR crossover and around larger manifest/auth-index boundaries; no hidden path-length, auth-tree, varint, or limit serialization transition may create an unsafe admission.

H3 — **explanatory precision**: for rows where the archive shape is unchanged except target length, predicted and actual delta should differ only by explicitly reported serialization-boundary residuals. Exact equality is preferred and reported, but H1/H2 are the safety gate.

H4 — **ONE invariant**: all candidate rows reconstruct exactly, are deterministic, and remain within `surprise/concat/repeat/fill/xor/add8`; no hidden reader codec or family-specific reader opcode is introduced.

A false reject is preserved and measured as lost opportunity. It does not make the model unsafe, but excessive false rejects mean the model is not useful enough to advance.

## Decision vocabulary

- `ADVANCE_MARGINAL_COST_ADMISSION_MODEL` only if H1, H2, H4 hold and the model admits at least one nontrivial ADD8/XOR opportunity while producing no false admits;
- `HOLD_MARGINAL_COST_ADMISSION_MODEL` if semantic structure is exact but the model is too conservative, materially inaccurate, or cannot explain serialization-boundary residuals;
- `RETIRE_OR_REPAIR_MARGINAL_COST_ADMISSION_MODEL` for any false admit, semantic failure, nondeterminism, hidden reader mechanism, or result-dependent calibration.

This decision does **not** modify the product writer. Product integration requires a separate experiment comparing current selection with the proposed admission gate, including creation CPU/wall/RSS and discovery/read traffic.

## Genesis exclusion

This is synthetic transfer research only. It must not import, generate, inspect, encode, compare, score, or infer any of the frozen 15 Genesis workloads. It must not execute v0.29 or v0.30 and cannot select a Genesis winner.

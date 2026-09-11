# ONE-G0.2 Crystallization economic admission writer — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED BEFORE WRITER-INTEGRATION RESULT**

## Mission lock

Hosted exact-source evidence for the frozen transfer marginal-cost model (`ADVANCE_MARGINAL_COST_ADMISSION_MODEL`) showed zero false admits, zero false rejects, zero boundary sign errors, and bounded residuals while using representation-cost terms rather than a learned crossover table. This experiment asks the next product-boundary question: can that model be used as an encoder-only admission gate so exact but economically losing Law nominations remain Surprise, without changing the reader-visible ONE algebra or harming useful Law opportunities?

This is a writer-selection experiment, not a Genesis run and not a product promotion by itself.

## Frozen admission model

The writer-side predictor is the already-preregistered affine marginal representation model:

`predicted_complete_delta = K_relation - target_length`

with fixed representation-cost terms from the isolated length-23 calibration construction:

- exact reuse: `K = -3` bytes;
- Fill: `K = 1` byte;
- ADD8(constant): `K = 11` bytes;
- XOR(constant): `K = 11` bytes.

These constants are not length thresholds or corpus-fit parameters. They estimate the fixed serialized representation cost of replacing target Surprise bytes with the corresponding generic ONE structure while retaining already-existing predictor state. No constant may be changed after the integration results are observed.

Admission rule: admit a proved Law only when predicted complete-wire delta is `<= 0`; otherwise retain the target as ordinary Surprise. Exact reuse and Fill are still evaluated by the same rule. The reader sees no new opcode, codec, dispatch table, or discovery behavior.

## Efficiency placement

For ADD8/XOR, once sparse sampling nominates a relation, a predicted economic rejection may occur before the full exact-proof scan. This is allowed and preferred: a relation known to be uneconomic does not need an O(n) proof merely to be discarded. The gate itself must be O(1) in target length and allocate no target-sized auxiliary buffer.

A sample failure follows the existing discovery path unchanged. A predicted admission still requires the existing exact proof before Law emission.

## Frozen transfer cases

Use only synthetic/transfer trees independent of Genesis. The matrix must include, at minimum:

1. tiny ADD8 at lengths 2, 4, 8, 9, 10 (known danger zone);
2. ADD8 at 11, 12, 16, 32, 256, 4096;
3. the same lengths for XOR;
4. Fill at lengths 1, 2, 8, 32, 4096;
5. exact reuse at lengths 1, 2, 8, 32, 4096;
6. unrelated deterministic pseudo-random pairs that must remain Surprise;
7. one mixed tree containing profitable and unprofitable opportunities together plus empty file, directory, executable mode and symlink.

The builder receives only the tree path and an encoder policy switch selecting current-vs-economic admission. It receives no family label, expected relation, expected result, crossover, workload identity, or Genesis information.

## Arms

A — **current selector**: existing `build_general_law_archive()` behavior with economic admission disabled.

B — **economic selector**: same writer, same sampling, same exact predicates, same manifest/authentication, same limits and same wire encoder, with only the frozen marginal-cost admission rule enabled.

Both arms must remain independently readable by the existing authenticated ONE reader.

## Measurements

For every transfer row preserve:

- complete persisted wire bytes for A and B;
- exact reconstructed filesystem semantics;
- deterministic wire;
- reader-visible op set;
- Law-class counts;
- Surprise bytes;
- control/integrity bytes;
- discovery sampled bytes;
- discovery exact-proof bytes;
- source-read bytes;
- build CPU time and wall time over repeated fresh constructions;
- peak RSS using a fresh-process measurement lane or an explicit `unavailable` marker if hosted isolation cannot be established honestly.

For the mixed tree additionally preserve total complete-wire delta and the number/type of opportunities retained vs rejected.

## Falsifiable hypotheses

H1 — **economic safety**: B must never produce more complete persisted bytes than A on any frozen transfer row. Tiny ADD8/XOR rows whose complete-wire Law form is regressing must become Surprise under B.

H2 — **opportunity preservation**: every row where the frozen model predicts non-regression and the relation is exactly proved must remain representable as the same generic Law family under B. Any false reject relative to the frozen model is HOLD.

H3 — **semantic/representation invariance**: A and B reconstruct the exact same filesystem, are deterministic, and B introduces no reader-visible operation outside `surprise/concat/repeat/fill/xor/add8`.

H4 — **proof-work pruning**: across the tiny ADD8/XOR rejection subset, B's `discovery_exact_proof_bytes` must be strictly lower than A's. Sampling traffic may remain equal. This is the causal compute-efficiency benefit expected from early economic rejection.

H5 — **creation-cost sanity**: B must not cause a confirmed creation regression under the repository normative timing rule in `docs/PERFORMANCE_RELEASE_GATE.md`: the median slowdown must exceed **both 5% relative and 3 ms absolute** to count as a timing regression. Improvements are reported, not required, because hosted microbench timing can be noisy.

### Pre-result amendment record

The first committed draft of this preregistration mistakenly used `>10% relative and >=1 ms absolute` for H5. While the exact-source integration run was still queued and before any writer-integration result was observed, the normative performance gate was reread and this mismatch was corrected to the repository-authoritative `>5%` **and** `>3 ms` rule. The admission constants, transfer matrix, byte gates, semantic gates, proof-work hypothesis, and decision vocabulary were not changed. This amendment is itself durable evidence and must not be rewritten after results arrive.

H6 — **reader/access non-regression by construction**: no new reader mechanism is introduced. For rows where A and B emit the same Law shape, wire equality is preferred and must be reported. For economically rejected rows, reader work may change only because the target is Surprise rather than a Law cone; selective-read behavior must remain valid and exact.

## Decision vocabulary

- `ADVANCE_ECONOMIC_WRITER_ADMISSION` only if H1-H4 hold, H3 has no hidden reader mechanism, and H5 does not trigger;
- `HOLD_ECONOMIC_WRITER_ADMISSION` for false rejects, confirmed creation regression, missing resource evidence, or mixed-tree interaction that prevents safe promotion;
- `RETIRE_OR_REPAIR_ECONOMIC_WRITER_ADMISSION` for any false admit that increases complete bytes, semantic failure, nondeterminism, hidden codec/opcode, result-dependent constant change, or Genesis leakage.

An ADVANCE permits a later, separate commit to make economic admission the default general-Law writer policy. It does not by itself authorize Genesis scoring or claim superiority over v0.29/v0.30.

## Genesis and comparator exclusion

This experiment must not import, generate, inspect, encode, compare, score, or infer any of the frozen 15 Genesis workloads. It must not execute frozen v0.29 or v0.30. The four Genesis status flags, if emitted, must remain false. Frozen comparators remain exactly `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` and `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.
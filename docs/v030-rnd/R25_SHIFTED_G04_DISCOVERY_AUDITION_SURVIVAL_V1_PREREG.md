# r25 Shifted G0-G4 discovery-audition survival v1 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE D3 QUESTION / R0 DISPROOF / ZERO PRODUCT OR RELEASE CREDIT**

Parent evidence: `docs/v030-rnd/R25_SHIFTED_G04_GRAPH_KERNEL_ATTRIBUTION_V3_RESULT.md`.

## Causal question

The valid v3 graph-kernel attribution showed that attempt-5 executes 1,369 delta auditions versus 972 for v0.28 while per-call delta cost is essentially unchanged (0.99674x). The 397 additional calls predict the observed ~11.14 s delta-time increase closely. What remains unknown is whether those additional position-independent discovery auditions materially contribute to the attempt-5 winning bytes.

This experiment asks one narrow question:

> If attempt-5 retains the inherited LSH candidate set but disables only the additional `_position_independent_candidates` discovery contribution, does the exact accepted attempt-5 archive remain byte-identical?

## Frozen arms

Target: `resemblance_hostile_v1/01_shifted_versions`, built through the same deterministic current release-performance corpus generator used by the parent attribution.

Three fresh-process alternating paired repetitions:

- **baseline** — unchanged `experiments.entropygraph_v029_residual_fast.build_graph`;
- **inherited-only** — same builder with `accepted.BASE.P._position_independent_candidates` temporarily replaced by a function returning no additional pairs. Inherited `lsh_candidates`, all delta/mosaic primitives, pack selection, residual packing, archive grammar and verification remain unchanged.

The instrument wraps `accepted.BASE.P.delta_encode` only to count calls and total delta wall time in each arm. The wrapper must return the exact underlying result and may not change arguments or bytes.

## Invariants / validity

A valid arm must:

1. strongly verify;
2. reconstruct the exact same tree SHA-256 as the baseline;
3. be byte-deterministic across all repetitions within that arm;
4. execute exactly one attempt-5 graph build per repetition;
5. report positive finite child time and delta time/call counts;
6. preserve all product semantics except the one discovery-source ablation in the inherited-only arm.

No product file is changed. This instrument has zero release credit.

## Frozen decision grammar

Let `B` be baseline archive bytes and `I` inherited-only bytes.

- `SHIFTED_DISCOVERY_AUDITIONS_BYTE_DEAD` iff `I == B` and inherited-only SHA-256 is identical to baseline SHA-256. This proves the additional discovery source is unnecessary for this exact winning Shifted artifact and authorizes an R3 exact-admission/futility Builder, subject to generalization.
- `SHIFTED_DISCOVERY_AUDITIONS_SIZE_CONTRIBUTING` iff `I > B` while both arms remain valid. Record the exact byte cost of removing discovery and do **not** prune the family; next work must identify which extra auditions survive and seek an exact lower bound/reuse mechanism.
- `SHIFTED_DISCOVERY_AUDITIONS_ALTERNATE_SMALLER` iff `I < B` while both arms remain valid. Preserve as surprising evidence and require hostile review before any product interpretation.
- `INVALID` for any identity, determinism, verification or instrument failure.

Timing is causal/supporting evidence only. It does not receive release credit. If the inherited-only arm removes at least 25% of baseline delta calls, S5 speculative-work dominance is considered supported for this exact Shifted regime only when its archive bytes are not worse.

## Strongest alternative explanations

- The 397 additional calls may be necessary for the 38,532 B attempt-5-vs-v028 saving; similar per-call cost alone cannot prove waste.
- Some additional pairs may seed a multi-base mosaic even when they are not selected as single-delta edges, so final archive identity—not merely single-edge acceptance—decides survival.
- The extra time could include correlated graph-control work outside `delta_encode`; call reduction is not itself a full product-speed claim.

## Handoff law

A byte-identical inherited-only result advances to a generalization/Builder prerequisite rather than immediate shipping. A size-contributing result blocks blanket pruning and redirects to exact audition-survival attribution or a pre-delta necessary-condition/lower-bound design. No threshold, corpus, locality rule, recovery/integrity guarantee or release criterion may change in response to the result.

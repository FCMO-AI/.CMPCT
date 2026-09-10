# ONE-G0.2 Crystallization wire-economics geometry — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED BEFORE RESULT-BEARING EXECUTION**

## Question

Automatic ONE discovery currently accepts exact reuse, Fill, ADD8(constant), and XOR(constant) after semantic proof, subject to selective-topology safety, but it does not yet expose a causal model of the complete persistent byte cost of Crystallization versus Surprise.

Before adding any size cutoff or tuning a selector, measure the wire-economics geometry on fixed transfer-only relation families. The goal is to identify whether each generic Law has a stable, explainable break-even shape that can later be compiled into a cheap marginal-cost admission test rather than a corpus-tuned threshold.

## Frozen transfer matrix

Lengths, in bytes:

`2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096, 16384`

Families:

1. exact reuse: target is byte-identical to a deterministic high-entropy Surprise source;
2. ADD8: target is source +37 modulo 256;
3. XOR: target is source XOR 0xA5;
4. Fill: one file containing repeated byte `Q`.

For the pair families, source bytes are deterministic SHA-256 stream bytes and source precedes target lexically. Each pair must use an independently Surprise-backed source. The builder receives only the tree path; it receives no family label, constant, expected source/target pairing, or admission hint.

## Arms

For every row build:

- candidate: `build_general_law_archive(tree)`;
- control: same-input authenticated Surprise-only `build_authenticated_archive(tree)`.

Count complete persisted `len(wire)` on both sides. No detached-payload accounting is sufficient.

## Mandatory reader-side proof

A row is scientifically admissible only if the opened candidate graph independently proves the intended structure:

- exact reuse -> source and target share one root reference;
- ADD8 -> target root op is `add8`;
- XOR -> target root op is `xor`;
- Fill -> file root op is `fill`.

Whole-tree reconstruction must be byte exact, wire deterministic, and reader-visible operations must remain within `surprise/concat/repeat/fill/xor/add8`.

## Measurements

For every family/length retain:

- candidate complete wire bytes;
- Surprise-only complete wire bytes;
- signed byte delta `candidate - control`;
- ratio;
- candidate/control wire SHA-256;
- reader-side structure evidence;
- writer discovery sample bytes and exact-proof bytes;
- source-read bytes and authentication reread bytes.

Summaries may identify the first measured non-regressing length per family, but that value is descriptive evidence only. This experiment MUST NOT itself change the product selector or declare a production threshold.

## Falsifiable hypotheses

H1: at least one tiny semantically valid Law row has positive complete-byte delta, demonstrating that predictability alone is insufficient for Crystallization.

H2: each pair Law family eventually becomes non-regressing at larger lengths under the current complete authenticated archive format.

H3: unrelated wire/semantic or hidden-op changes are not required to obtain the crossover; all wins/losses arise inside the same ONE ontology.

Disproof is preserved. If H1 is false, do not invent a tiny-file problem. If H2 is false for a family, that family lacks demonstrated complete-wire economics under this seam and must remain research debt.

## Decision vocabulary

This is descriptive causal evidence, not candidate promotion:

- `ADVANCE_CRYSTALLIZATION_ECONOMICS_MODEL` if semantics/structure/determinism are exact and H2 holds for every family;
- `HOLD_CRYSTALLIZATION_ECONOMICS_MODEL` if semantics are exact but one or more families never becomes non-regressing in the frozen range;
- `RETIRE_OR_REPAIR_CRYSTALLIZATION_ECONOMICS_MODEL` for semantic, reader-structure, ontology, or determinism failure.

H1 is reported separately and does not determine ADVANCE/HOLD by itself.

## Genesis exclusion

This matrix is synthetic transfer data only. It must not import, generate, inspect, encode, compare, score, or infer any of the frozen 15 Genesis workloads. It must not execute v0.29 or v0.30 and cannot select a Genesis winner.

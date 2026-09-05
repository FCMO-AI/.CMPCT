# ONE-G0.2 — Stratified branch-bound proof topology result

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Decision:** `advance_stratified_proof_topology`  
**Result-bearing source:** `edc369d0997f4f1cfe5d53d08fcc565b71b45bfd`  
**Workflow:** `33961206488`  
**Job:** `101293285998`  
**Artifact:** `9967996212`  
**Artifact zip SHA-256:** `ea4a58b87b7cff1c65644736e9659d1c61753a080eb6e68771451004f6efc57a`

## Hypothesis

The preceding immutable hostile transfer proved that a fixed-front exact-proof topology can miss a globally useful shift relation when a small contiguous prefix owns all sixteen proof attempts. The superseding Builder kept the successful one-byte coverage stage and all frozen admission/cost limits, but divided proof ownership across sixteen equal relation strata, allowing at most one coverage-supported exact 64-byte proof per stratum.

Promotion of the research topology required all of the following simultaneously:

- exact classification agreement with the minimizer-vs-fixed marginal opportunity oracle across the inherited branch-bound matrix;
- recovery of positive marginal reuse after independent front, middle and tail contiguous 1 KiB damage;
- rejection of the 32-byte fragmented false-shift pattern;
- retention of the 96-byte fragmented positive control;
- at most four successful proofs required for admission and at most sixteen proof attempts total;
- gate elapsed <=5% of promoted incremental selector cost on eligible rows;
- modeled gate read traffic <=25% of input;
- unchanged ONE reader-visible semantics.

## Exact-head result

`tests/one`: **76 passed**.

The frozen transfer passed and emitted `advance_stratified_proof_topology`.

### Hostile phase recovery

| Case | Marginal opportunity | Proofs | Attempts | Gate / incremental selector | Modeled read fraction | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| front 1 KiB damage, +1 shift | 64,512 B | 4 | 4 | 0.729% | 8.209% | enable |
| middle 1 KiB damage, +1 shift | 64,511 B | 4 | 4 | 0.707% | 8.173% | enable |
| tail 1 KiB damage, +1 shift | 64,511 B | 4 | 4 | 0.719% | 8.179% | enable |

The retired fixed-front topology produced **0 exact proofs** on the corresponding front-damaged relation despite 64,512 B of real marginal opportunity. The new topology therefore repairs the exact causal failure without increasing the sixteen-attempt ceiling.

### False-pattern discrimination

- `false_fragmented_shift_every32`: **0 B** marginal opportunity, 16 attempts, **0 exact proofs**, gate disabled; cost ratio **0.713%**, modeled read fraction **8.197%**.
- `fragmented_shift_every96_control`: **760 B** marginal opportunity, 12 attempts, **4 exact proofs**, gate enabled; cost ratio **0.710%**, modeled read fraction **8.606%**.

Thus distributed proof ownership did not buy robustness by accepting the known sparse-resemblance false positive.

### Ordinary negative controls

- random 1 MiB: no marginal opportunity, gate disabled, **0.772%** of incremental selector cost, **7.792%** modeled read fraction;
- zlib-random payload: no marginal opportunity, gate disabled, **0.688%** cost ratio, **7.792%** read fraction;
- zero 1 MiB: no marginal opportunity, gate disabled, **0.683%** cost ratio, **1.563%** read fraction.

### Positive shifted controls

- ordinary one-byte-shifted version pair: **524,288 B** marginal opportunity, 4/4 exact proofs, **0.753%** cost ratio, **7.835%** read fraction;
- zero-anchor shifted 8 KiB starvation case: **8,192 B** marginal opportunity, 4/4 exact proofs, **2.218%** cost ratio, **10.937%** read fraction;
- hostile +/-1 and +/-2 64 KiB shift relations: **65,534–65,535 B** marginal opportunity, 4 proofs in 4–5 attempts, approximately **0.704–0.750%** cost ratio and **8.174–8.191%** modeled read fraction.

All observed eligible rows remained far inside the frozen 5% compute and 25% read ceilings.

## Scientific interpretation

This result supports a narrower and stronger statement than “the shift gate works.”

1. The cheap global coverage signal can nominate a signed displacement at a small fraction of the current incremental selector cost.
2. Exact proof remains necessary: the 32-byte fragmented pattern has overwhelming one-byte +1 resemblance but zero reconstructable marginal opportunity.
3. Concentrating bounded proof work at one spatial phase is avoidable debt. Distributing proof ownership across independent support regions restores robustness to contiguous local damage without adding proof budget or reader complexity.

The useful principle is **distributed evidence ownership under a bounded proof budget**, not this half-to-half test layout itself.

## Strongest surviving criticism

The experiment still assumes one known half-to-half relation and only the signed displacement set `{-2,-1,+1,+2}`. It therefore proves a writer-side admission pattern, not a general candidate generator. Sixteen deterministic strata can also be adversarially targeted if an attacker knows the exact placement. The result is robustness evidence against contiguous localized corruption, not a cryptographic or worst-case proof-placement guarantee.

The next scientific step must not multiply special-case shift opcodes. It should measure whether this branch-and-bound admission law can sit in the **fused ONE observation/discovery path** and reduce total encoder work while preserving the exact generic reuse Laws ultimately emitted.

## Next decisive test

Build an end-to-end A/B around the current promoted tail-return selector/discovery baseline:

- baseline: current promoted fused discovery path;
- candidate: same path with cheap shift-coverage nomination + stratified exact proof used as an early branch-and-bound route to a generic exact reuse Law;
- charge complete creation/discovery CPU, memory traffic/state, proof bytes and emitted opportunity;
- preserve random/incompressible, already-compressed, repeated/fixed, ordinary shifted, starvation-shifted, fragmented false-pattern and contiguous-damage controls;
- fail if any inherited opportunity disappears, false-pattern work becomes unbounded, or total encoder cost merely moves into another stage.

The question is no longer whether the proof topology can recognize the relation. It is whether it produces **positive marginal information yield per unit of total encoder work** once integrated with the real discovery path.

## Claim boundary

No reader-visible ONE operation, CMPCT format, release comparator or canonical version changed. This is writer-discovery research evidence only and grants no v0.29/v0.30 superiority or release authority.

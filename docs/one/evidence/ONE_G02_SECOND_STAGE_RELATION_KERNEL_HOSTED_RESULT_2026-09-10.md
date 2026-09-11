# ONE-G0.2 second-stage relation falsifier — hosted result

Date: 2026-09-10
Status: durable hosted evidence; **kernel remains HOLD**
Branch/source: `research/cmpct1` @ `ca61df66c9c59a9258cdac5e8bb0676cc351a0e7`
Workflow run: `34533096098`
Job: `103058283334`
Artifact: `10174598899`
Artifact SHA-256: `f496bbed4b5318b3957d0e2eb551164b5893fb520d8f9e824973af427a9a2bd0`
Experimental version: `ONE-G0.2`

## Mission lock

Question: can a second sparse relation falsifier reduce expensive exact-proof work for false ADD8/XOR nominations without becoming a semantic authority or exporting unacceptable survivor overhead?

Hard invariants:

- exact proof remains the only positive semantic authority;
- no new reader opcode or discovery burden;
- false candidates must never survive as Law;
- primary and second-stage geometry must remain independently checkable;
- modeled traffic and hosted CPU/wall costs remain visible, including hostile survivors;
- this experiment is not a Genesis comparison and does not execute Genesis inputs.

Disproof rule: preserve HOLD/RETIRE if hostile-survivor overhead breaches the preregistered kernel gates even when easy false candidates become much cheaper.

## Hosted evidence

The exact-source workflow completed successfully on Ubuntu 24.04 / Python 3.12.14. All 15 hostile/unit tests passed.

### Independent information-yield oracle

Decision: `ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY`.

The frozen 16-point primary geometry and independent midpoint stage preserve true ADD8/XOR Laws, kill stage-2 collision rows, and honestly allow dual collisions to reach exact proof.

Across the eight modeled stage-2-kill rows:

- exact-proof bytes avoided: **83,072 B**;
- added second-stage bytes: **240 B**;
- per-row modeled speedup ranged from **2.1333x** at 32 B to **1092.2667x** at 16 KiB.

This is a traffic oracle, not a product/runtime claim.

### Isolated relation-kernel A/B

Decision: `HOLD_SECOND_STAGE_RELATION_KERNEL`.

Gates:

- H1 correctness: PASS
- H2 hostile benefit: PASS
- H3 survivor debt: **FAIL**
- H4 broad kernel economics: PASS
- H5 geometry sensitivity: PASS

Summary:

- broad median CPU ratio: **0.5919106327x**
- broad median wall ratio: **0.6302496395x**
- first-kill median CPU ratio: **0.05381970885x**
- first-kill median wall ratio: **0.08099058493x**
- last-kill median CPU ratio: **0.005010526219x**
- last-kill median wall ratio: **0.006092958928x**
- hostile-survivor median CPU ratio: **1.555511111x**
- hostile-survivor median wall ratio: **1.410625355x**

The causal result is mixed but decisive: the sparse stage is extremely effective when it kills a false nomination, but its current Python implementation imposes too much fixed/control overhead when a dual-collision candidate survives and baseline exact proof fails very early. This prevents writer promotion in the tested form.

### Dual-collision tail supplement

Decision: `ADVANCE_SECOND_STAGE_DUAL_COLLISION_TAIL_SAFETY_ONLY`.

All correctness/accounting/per-row/broad survivor-tail gates passed.

Summary:

- median CPU ratio: **1.0004547229x**
- median wall ratio: **1.0003380593x**
- worst CPU ratio: **1.0141647265x**
- worst wall ratio: **1.0140687798x**
- maximum modeled extra sparse traffic: **30 B**

This shows the second stage does **not** materially tax expensive late-failing exact proofs: once the baseline already scans nearly the entire relation, the extra 15 midpoint checks are essentially amortized. The red is therefore not an inherent `+30 B` cost at large proof depth; it is specifically the interaction between fixed sparse-stage/control overhead and candidates that baseline would reject very early.

## Hostile review / strongest negative

Do not summarize this experiment as "stage 2 is faster". That would erase the most important row class.

The surviving dual-collision-early geometry is the present blocker: on those rows, baseline exits after encountering an early mismatch while the candidate first pays the entire sparse second stage and then enters exact proof. Hosted survivor median is ~**1.56x CPU / 1.41x wall**.

The tail supplement falsifies a tempting but wrong interpretation that any dual-collision survivor is intrinsically expensive. Late survivors are near-neutral. The cost depends on **where exact proof would have failed**, i.e. saved proof distance versus sparse/control cost.

## Next decisive hypothesis

Hypothesis: a second-stage rejector should run only when a conservative lower bound on expected exact-proof work is large enough to amortize its fixed/control cost. This should be derived from already-paid evidence or proof-distance expectation, not from workload identity or a magic file-size threshold.

Candidate solution classes to falsify:

1. **Proof-distance-aware admission:** estimate a lower bound on exact-proof bytes likely to be consumed before mismatch; skip stage 2 when baseline can cheaply disprove the relation.
2. **Fused-observation reuse:** derive the second-stage evidence from an observation sketch already paid for, eliminating separate sparse loads/control.
3. **Native/bulk stage-2 kernel:** preserve the same information test but remove Python loop/call overhead; promotion still requires the hostile-survivor gate, not merely lower microbenchmark overhead.

Preferred next experiment: isolate whether the red is dominated by Python fixed/control overhead or unavoidable extra memory traffic. Construct a same-geometry native/bulk or fused-evidence A/B with early/late/true/stage2-kill rows and retain exact proof as sole authority. Kill the idea if early-survivor debt remains materially above the preregistered envelope after fixed overhead is removed.

## Genesis boundary

This result executes no Genesis workload and selects no Genesis winner. Frozen comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No claim from this receipt substitutes for the required 15-workload same-input, same-semantics Genesis gate.
# v0.30 EG08 low-yield work attribution Mission Lock — 2026-09-13

Status: **preregistered causal attribution; research only**

## Entering evidence

The independently frozen eligible-nine transfer showed that EG08 saves `1,736,562 B` versus EG07 with zero stored-byte regressions, unchanged locality geometry, strong verification and recovery, but the current implementation fails the preregistered low-yield creation-cost rule. Two rows are especially diagnostic because they were identified by that pre-existing gate, not chosen after this attribution:

- neutral `10_large_mixed_binary`: only **56 B** saved while EG08 historically used about `3.019x` EG07 creation CPU;
- hostile `05_incompressible`: **0 B** saved while EG08 historically used about `2.604x` EG07 creation CPU.

EG11 subsequently reproduced EG08 byte-for-byte with lower aggregate creation work, but its ~1.32% aggregate improvement is far too small by itself to explain or close those multi-x low-yield ratios.

## Question

On those two frozen low-yield surfaces, is the fixed `(3,6,12,19)` effort ladder expensive mainly because it computes candidate frames that are ultimately discarded, or because the frames that must be retained to preserve exact EG08 bytes are themselves expensive?

This is attribution, not a new selector. No level, threshold, pack geometry, admission law or product byte is changed.

## Method

For every non-hot EG07 physical pack on the two frozen surfaces:

1. preserve the exact EG07 current storage choice;
2. execute the exact EG08 ladder and unchanged `compressed + 8 < raw` admission law;
3. time every individual compression rung in process CPU and wall time;
4. reproduce EG08's best-so-far/tie/first-worse decision exactly;
5. classify each executed rung after the final decision as:
   - **final-selected work**: the rung produced the exact final payload stored by EG08;
   - **superseded work**: the rung temporarily improved/tied the incumbent but was not the final selected payload;
   - **rejected work**: the rung never became the best stored choice;
6. require the reconstructed final codec/payload for every pack to equal the actual EG08 artifact exactly.

The timing instrumentation itself is not a performance claim. The useful quantity is the share of measured compression work by outcome class under one execution.

## Falsifiable hypotheses

H1 — **rejected-work dominated**: more than half of measured ladder CPU on each zero/near-zero-yield surface is spent on rungs whose bytes are not present in the final EG08 archive (`superseded + rejected > final-selected`). This supports a future exact opportunity-bound / work-reuse Builder.

H2 — **selected-work dominated**: final-selected rung CPU is at least half of measured ladder CPU on a low-yield surface. Then exact-EG08 creation has a material intrinsic cost floor on that surface; a future improvement cannot eliminate most of the debt merely by skipping losers while keeping identical bytes.

The natural 50% split only classifies where most measured work goes. It is not a product admission threshold and must never be reused as one.

## Required evidence

For both surfaces record:

- deterministic source fingerprint;
- EG07 and EG08 complete archive bytes;
- exact reconstructed EG08 pack-payload identity;
- number and CPU/wall time of all ladder calls;
- final-selected, superseded and rejected call counts/time;
- selected storage saving;
- early-stop count;
- hot/stream exclusions;
- locality geometry;
- build-time strong verification.

Any mismatch to actual EG08 bytes makes the attribution `INVALID` and grants no causal conclusion.

## Verdict vocabulary

- `EG08_LOW_YIELD_REJECTED_WORK_DOMINATES`
- `EG08_LOW_YIELD_SELECTED_WORK_DOMINATES`
- `EG08_LOW_YIELD_MIXED_WORK`
- `EG08_LOW_YIELD_ATTRIBUTION_INVALID`

No verdict promotes a representation or changes a release score. It only selects the next mechanism class.

## Preservation

No Genesis score, v0.29 comparator, locality ceiling, integrity/recovery semantics, format revision, numeric version or ONE evidence changes in this experiment.

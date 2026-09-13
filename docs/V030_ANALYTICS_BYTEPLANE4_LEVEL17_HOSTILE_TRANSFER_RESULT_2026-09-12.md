# v0.30 BytePlane4 + level-17 hostile transfer result — 2026-09-12

Status: **negative generalization verdict with a positive structural signal; no product/release credit**.

Source head: `61bbd3be0745629aec4994545afd85ed69cbf7d6`
Hosted run: `34731592505`
Schema: `cmpct-v030-analytics-bp4-l17-hostile-transfer-v1`

## Frozen test

The positive Analytics seed froze Zstd level 17, BytePlane width 4, the exact level-1 framed audition and exact economic fallback. The hostile transfer changed none of those parameters and used two generator-distinct structured positives plus two entropy-dense false friends.

The preregistered transfer verdict required both positives to select the transform, become smaller than direct L17, and complete verified creation at least 20% faster than direct L19. Both negatives had to select zero strong transforms and remain byte-identical in size to direct L17.

## Exact hosted result

### Positive: `counter32`

- direct L17: **2,098,705 B**, **0.0867041805 s** verified create
- fixed BP4+L17: **42,677 B**, **0.4770492195 s**
- direct L19: **2,098,705 B**, **0.1101423670 s**
- selected transforms: **8/8 strong auditions**
- raw transformed bytes: **2,097,152 B**
- net payload saving: **2,056,148 B**
- strong transformed-payload **Zstd-17 compression** CPU: **0.3783257385 s**
- speedup versus L19: **-333.12%**

The representation signal is enormous, but recompressing the already shuffled payload at level 17 dominates the whole job and violates the frozen speed gate.

### Positive: `mixed32`

- direct L17: **325,012 B**, **0.2365438170 s**
- fixed BP4+L17: **5,572 B**, **0.2475473875 s**
- direct L19: **329,318 B**, **0.3192397210 s**
- selected transforms: **8/8**
- net payload saving: **319,440 B**
- speedup versus L19: **22.46%**

This positive passed all of its frozen transfer gates.

### Negative: `random32`

- direct L17 / candidate / direct L19: **2,098,704 B** each
- cheap winners: **0**
- strong auditions/selections: **0 / 0**
- candidate equals direct L17 exactly

### Negative: `precompressed`

- direct L17 / candidate / direct L19: **2,098,705 B** each
- cheap winners: **0**
- strong auditions/selections: **0 / 0**
- candidate equals direct L17 exactly

Both false friends passed the frozen rejection contract.

## Verdict

**`RETIRE_BP4_L17_GENERALIZATION_CLAIM`**.

The verdict is negative because `counter32` failed the preregistered speed requirement. The result must not be repaired by changing width, level, positive threshold or fixture identity.

However, the causal failure is narrower than “BytePlane4 does not generalize.” The fixed representation produced very large byte wins on both independently generated structured positives and zero false positives on both entropy-dense negatives. The failure was execution cost inside the transformed-payload strong encode.

A hostile review of the exact implementation corrected an initially tempting but wrong diagnosis: `_shuffle4()` is performed before the `strong_transform_cpu_s` timer, during the cheap level-1 audition. The reported ~0.378 s on `counter32` therefore **cannot be attributed to Python byte-plane shuffling**. It is the subsequent Zstd-17 compression of the already shuffled payload. This correction is important because optimizing the transpose would attack the wrong bottleneck.

The cheap audition has already paid for `plane1 = Zstd-1(BytePlane4(raw))`. The next causal question is therefore whether those already-computed `plane1` bytes can be reused as the final transformed representation when they also beat direct level 17, eliminating the redundant transformed level-17 encode entirely. That is a direct ONE-style fused-observation/reuse hypothesis, not a new selector or representation width.

## Next decisive action

Freeze level 17, width 4 and the same cheap audition. Build an **audition-reuse referee** in which a cheap-gate winner may store the already-produced framed level-1 transformed payload directly if it is strictly smaller than direct level 17. No transformed level-17 recompression is allowed in the candidate.

First test the frozen Analytics workload against direct L17 and the prior strong BP4+L17 seed. Continuation requires crossing the accepted-v0.29 byte floor while materially reducing complete verified creation. If Analytics cannot retain the byte floor, retire audition reuse without tuning. If it can, rerun the exact same hostile fixtures unchanged; `counter32` then becomes a particularly strong falsifier because its prior failure was almost entirely transformed-payload level-17 work.

No aggregate v0.30 score changes. `research/cmpct1` and the frozen ONE Genesis result remain untouched.

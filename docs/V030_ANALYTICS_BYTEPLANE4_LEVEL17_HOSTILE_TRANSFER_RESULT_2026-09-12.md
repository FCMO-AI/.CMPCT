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
- strong-transform CPU: **0.3783257385 s**
- speedup versus L19: **-333.12%**

The representation signal is enormous, but the current Python transform execution dominates the whole job and violates the frozen speed gate.

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

However, the causal failure is narrower than “BytePlane4 does not generalize.” The fixed representation produced very large byte wins on both independently generated structured positives and zero false positives on both entropy-dense negatives. The failure was execution cost: on the largest counter fixture, strong BytePlane transformation alone consumed about 0.378 s while the entire direct-L19 verified creation took only about 0.110 s.

That distinction redirects work from selector/representation tuning to **bulk transform execution**. It is consistent with the existing native-core roadmap and with the ONE-derived lesson to move repeated byte-oriented work out of Python hot loops when the representation has already earned its existence.

## Next decisive action

Do not modify the frozen representation or selector. Profile the exact width-4 forward/inverse transform implementation and build a byte-identical bulk implementation using a low-level contiguous operation (first a vectorized/slicing lower-bound referee, then native C/Rust only if the lower bound is material). The experiment must hold compressed bytes and transform selection constant and measure only transform CPU/wall/RSS.

The target is causal: determine whether implementation overhead, rather than the representation itself, explains the `counter32` failure. If a byte-identical bulk transform cannot recover most of the 0.378 s cost, retire transform-execution optimization and preserve the seed as an Analytics-specific research result. If it can, transfer the faster primitive back to the frozen Analytics seed and rerun the same hostile fixtures unchanged.

No aggregate v0.30 score changes. `research/cmpct1` and the frozen ONE Genesis result remain untouched.

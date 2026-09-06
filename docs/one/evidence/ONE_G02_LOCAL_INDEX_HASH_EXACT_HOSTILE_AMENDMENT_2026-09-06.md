# ONE-G0.2 exact local-index hash — hostile-review amendment

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Trigger

The first exact-source execution of the frozen local-index hash A/B (run `34008374000`, source `41e099e1933ab27960765e1993614a7502df068d`) did not reach a performance result. The semantic audit aborted at `(8192, 29, damage_quarter)` because the candidate open-address locator returned an internal error after its 128 buckets contained no never-used slot.

The failure is a Builder defect, not evidence that the 64-entry local policy itself is inexact: the authoritative 64-entry ring remained bounded, while accumulated tombstones made an absent-key lookup scan all 128 buckets and return the implementation's `-2` saturation code. Open addressing with tombstones must treat this state as a maintenance event, not as proof that the key map cannot represent the still-bounded ring.

## Frozen repair boundary

No scientific threshold, state cap, corpus, timing gate or semantic requirement changes.

The candidate remains:

- the exact same authoritative 64-entry ring;
- the same 128 locator buckets;
- the same hash/mapping policy;
- exact hit/miss and prior-position parity with the linear baseline.

The only permitted repair is **bound-triggered locator rebuild**: if an absent-key lookup exhausts all 128 buckets because tombstones have removed every never-used sentinel, rebuild the locator from the authoritative live ring and retry. The rebuild must be charged inside candidate elapsed and probe/work accounting. It may not increase the 128-bucket bound or drop/alter a live ring entry.

This repair is deliberately triggered by representational saturation, not by a tuned tombstone percentage. It therefore cannot be adjusted after timing results to move a crossover.

## Authority

Run `34008374000` is authoritative evidence of the implementation defect and remains preserved as negative engineering history, but it has **no performance authority** because the candidate aborted before completing the frozen matrix.

A repaired run may consume performance authority only if it first passes the unchanged semantic gates and the collision-hostile stream. If the charged rebuild makes the candidate fail elapsed/probe/state gates, the result is a genuine rejection of this locator shape rather than grounds for further threshold tuning.

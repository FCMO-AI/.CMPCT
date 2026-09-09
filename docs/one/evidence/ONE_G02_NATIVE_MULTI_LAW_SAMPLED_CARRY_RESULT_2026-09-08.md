# ONE-G0.2 native sampled multi-Law carrying-cost result

**Decision:** `INVALIDATE_NATIVE_MULTI_LAW_SAMPLED_CARRY`  
**Exact source:** `d518fa6d6368f81fb1a6cc432400ed0a97623505`  
**Workflow run:** `34306436120`  
**Job:** `102323991001`  
**Artifact:** `10086807812`  
**Artifact digest:** `sha256:1b4c36e81369bc7902f258dc1757dd05c37ceee5625c16758aef7c24be89dd2e`

## Result

Exact source binding and the preregistered semantic tests passed. The frozen 30-cell hosted falsifier then returned INVALIDATE, not HOLD.

The sampled arm updated add8/XOR histograms only at positions `p & 3 == 0`, using the preregistered worst-case 1/2 sampled-support threshold. This did reduce relation-bearing cost versus the full per-byte observer: median sampled/full wall on the four relation families was about **0.83146x** and CPU about **0.83163x**.

That improvement is not admissible because semantics diverged. On `add8_ramp` at 64 KiB, 256 KiB and 1 MiB, the full semantic oracle nominated `reuse + add8`, while the fixed-grid sampled arm nominated `reuse + add8 + xor`. The sample grid aliases the arithmetic ramp into an apparent lag-64 XOR relation. This is a genuine cross-family false nomination created by sampling geometry, not an oracle defect.

Even ignoring the semantic invalidation, performance still missed the frozen carrying envelope:

- median sampled/baseline wall: **1.39467x** vs <=1.20x;
- median sampled/baseline CPU: **1.39438x** vs <=1.20x;
- worst sampled/baseline wall: **1.52667x** (`add8_ramp`, 256 KiB) vs <=1.35x;
- minimum 1 MiB sampled throughput: **241.84 MiB/s** vs >=250 MiB/s.

Representative 1 MiB wall ratios (sampled / run+reuse baseline):

- long_runs: 1.353x;
- exact_repeat: 1.360x;
- add8_ramp: 1.412x;
- xor_chain: 1.512x;
- mixed_structured: 1.391x;
- random: 1.247x;
- compressed_like: 1.248x;
- false_pattern: 1.243x;
- add8_phase_poison: 1.410x;
- xor_phase_poison: 1.514x.

## Interpretation

The negative is stronger than “sample harder.” A fixed positional grid can alias one real Law family into another, and the remaining lag-ring/control cost is still large enough that simply reducing histogram writes does not rehabilitate the carrying economics.

Therefore fixed-grid relation sampling is closed as a reopening path for this observer. Do not repair this result by suppressing XOR specifically on arithmetic ramps, changing the semantic oracle, relaxing the 1.20x/1.35x gates, or special-casing the synthetic families.

## Next reopening class

The next useful experiment should avoid per-byte lag state and fixed positional sampling altogether. A stronger direction is a **block-level relation sketch fused into the already-required 64-byte fingerprint cadence**: derive a very small number of relation invariants or lane probes when a chunk fingerprint is finalized, then launch exact bounded span growth only when those block sketches agree. The test must include cross-family alias controls, phase-shifted relations, late/sparse relations, random/compressed controls, and must measure false-positive proof work plus final bytes eliminated per CPU second.

That direction reuses work the observer already pays for rather than adding a second per-byte state machine. It remains writer-internal nomination only; exact proof is mandatory and no reader-visible mechanism changes.
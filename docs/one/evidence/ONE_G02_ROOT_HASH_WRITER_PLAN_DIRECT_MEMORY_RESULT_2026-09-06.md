# ONE-G0.2 root-hash writer plan-direct creator-memory terminal result — 2026-09-06

## Decision

`reject_plan_direct_creator_memory_claim`

The plan-direct V2 writer remains a promoted experimental **speed** advance. This result rejects only the broader claim that removing Python `Program` / `Node` / `Ref` materialization also produces a material, general creator-side Python peak-allocation reduction under the frozen matrix.

## Exact-source authority

- Branch: `research/cmpct1`
- Experimental line: `ONE-G0.2`
- Preregistration commit: `50cc802f03159aebeed8021fb59dd36b9c1adea2`
- Builder commit: `d8b9ec873af68de12c7f6be6a3725307818a7d47`
- Exact workflow/source head: `9a32f530046b4223e7979d62a90cc2e20961a518`
- Workflow run: `34043739117`
- Job: `101514976689`
- Artifact: `9992467270`
- Artifact digest: `sha256:de38031e583c36ba6559be9d154d27658453fb4b4bc9f72d3e1fe77d44a8dd9f`
- Full ONE semantic/hostile suite: passed before the measurement step
- Semantic failures in the memory audit: `0`
- Measurement scope: creator-side **Python traced peak allocation only** (`tracemalloc`)
- Samples per arm/row: `9`

The Actions job is red because the frozen measurement step exits non-zero when the preregistered advance gate fails. Setup, installation, the ONE test suite, and evidence upload all completed successfully. This is a scientific negative, not a broken harness.

## Frozen gates

For mature productive rows (64/128/256 KiB), advance only if all are true:

- median candidate/baseline traced-peak ratio `<= 0.80x`;
- no mature productive row `> 1.03x`;
- median absolute saving `>= 32 KiB`;
- mature control median `<= 1.03x`;
- no mature control row `> 1.08x`.

No thresholds were changed after observing the result.

## Terminal measurements

- mature productive median ratio: **`0.9579590283x`** (~4.20% lower traced peak);
- mature productive worst ratio: **`0.9984523353x`**;
- mature productive median absolute saving: **`19,108 B`**;
- mature control median ratio: **`0.9985147048x`**;
- mature control worst ratio: **`0.9992552904x`**.

The candidate therefore clears the no-regression bounds but misses both materiality gates: `0.95796x` is far above the required `0.80x`, and `19,108 B` is below the required `32 KiB` median saving.

## Workload heterogeneity

The negative is not equivalent to “Program materialization never matters.” The frozen rows expose a useful causal split.

### Fragmented /96

This plan/node-heavy case shows substantial absolute savings:

| Relation bytes | Baseline peak | Candidate peak | Saving | Ratio |
|---:|---:|---:|---:|---:|
| 64 KiB | 612,678 B | 516,030 B | 96,648 B | 0.842253x |
| 128 KiB | 1,187,797 B | 1,037,345 B | 150,452 B | 0.873337x |
| 256 KiB | 2,267,771 B | 1,894,931 B | 372,840 B | 0.835594x |

### Damage-quarter

Savings scale, but much more weakly:

- 64 KiB: `10,060 B`, `0.956254x`;
- 128 KiB: `19,108 B`, `0.957959x`;
- 256 KiB: `37,792 B`, `0.958281x`.

### Sparse-plan / controls

`shift_plus1` saves only about `868 B` in the mature range, while `fragmented_every32` and `independent_random` controls save `832 B` per row and remain approximately `0.997–0.999x`.

## Causal interpretation

The V2 plan-direct compiler removes a real object-graph cost, but Python `Program` / `Node` / `Ref` materialization is **not the broad peak-allocation owner** of this creator boundary. Input/source/target storage, native-plan/segment buffers and other retained writer state dominate peak allocation in many rows, so deleting the Program graph moves elapsed time far more than it moves the traced peak.

That distinction is valuable because the exact same V2 mechanism previously achieved a mature productive writer elapsed ratio of **`0.7807797801x`** (~21.92% less elapsed) while keeping canonical ONE0 bytes byte-identical. The speed advance therefore remains intact; this lane merely falsifies an unearned memory extrapolation from it.

The `fragmented_every96` rows show that object-graph materialization *can* own meaningful memory when node/plan density becomes high. That is explanatory evidence, not an adaptive-selector promotion. No post-hoc “use V2 only for fragmented inputs” memory claim is authorized by this result.

## Scope and non-claims

This result does **not** measure or claim:

- process RSS;
- native C allocation peak;
- system memory traffic/cache behavior;
- decoder/read memory;
- filesystem/product-level creator peak;
- arbitrary/fused discovery memory;
- v0.29/v0.30 superiority.

Stored bytes, canonical wire, decode semantics, selective-read behavior and reader complexity remain unchanged by V2 because its emitted bytes are identical to the Program-materializing writer.

## Hostile review

- The memory hypothesis was preregistered independently after the speed result; the speed win was not retroactively treated as a memory win.
- All semantic checks remained exact; no byte, plan, admission, relation-traffic, segment, hierarchy or reconstruction requirement was weakened.
- The broad memory gate failed and remains failed despite several individually favorable rows.
- A later RSS/native lane would need its own preregistration; `tracemalloc` cannot authorize that broader claim.

## Next decisive work

Keep plan-direct V2 as the experimental canonical writer compiler because its exact-source speed evidence is strong. Do **not** spend the next lane trying to squeeze the failed broad Python-memory gate by thresholds or workload classification.

Re-profile the improved writer/system boundary with V2 in place and attack the next measured elapsed/resource owner. In particular, move outward from the adjacent-version root-hash writer toward the current fused discovery + canonical writer boundary, preserving byte-identical ONE semantics and charging discovery, plan storage, canonical emission and creator resources together. The goal is to determine whether the ~21.9% writer-compiler gain survives at the broader creator boundary and what now owns the remaining wall time/peak resource cost.

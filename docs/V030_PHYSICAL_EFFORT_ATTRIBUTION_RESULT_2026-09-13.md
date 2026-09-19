# v0.30 physical compression-effort attribution result — 2026-09-13

Status: **accepted causal research evidence; no release/R4 credit**

Measured head: `10023cee076fe4372f08e8ea4b8e26ca073d4394`

Hosted run: `34771326919`

Artifact: `10321674239`

Artifact digest: `sha256:b85bcf5be0af8db929136414f0c790d7ad792588c07045b7827dcab858dcdfb8`

Scientific verdict: **`PHYSICAL_EFFORT_DOMINATES`**

Observed libzstd: **1.5.5**

## Frozen question

The Office control-plane attribution showed that implicit-v4 closes only ~0.38% of same-run Office regret when physical membership/payload is held fixed. H-EFFORT-1 therefore asked whether the remaining dominant Office/Analytics gap is primarily caused by the current v0.30 level-1 compression-effort cap rather than by pack membership/locality geometry.

This oracle froze every raw physical pack byte, pack boundary, membership relation, filesystem control and decode unit. It then recompressed those exact raw physical units at current level 1 and mature level 19. Level 1 had to reproduce every current codec choice and payload byte-for-byte before any counterfactual received credit.

The frozen historical control was again executed through the exact Genesis v0.29 facade `experiments/entropygraph_v029_residual_strict.py` from source `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` under the fail-closed source seal.

## Result

Both surfaces passed exact level-1 reproduction and retained the current verified/locality/recovery evidence. The level-19 result is a **counterfactual byte oracle on identical raw units**, not a materialized product archive.

| Surface | Current complete | Frozen v0.29 | Same-unit L19 counterfactual | Regret recovered | Classification |
| --- | ---: | ---: | ---: | ---: | --- |
| Office | `6,437,559 B` | `5,954,929 B` | **`5,952,840 B`** | **`484,719 B` (100.43%)** | `EFFORT_DOMINATES` |
| Analytics | `7,095,737 B` | `6,135,172 B` | **`6,135,280 B`** | **`960,457 B` (99.99%)** | `EFFORT_DOMINATES` |

At fixed geometry, level 19 therefore explains essentially the entire remaining density deficit on the two workloads that dominate Genesis gross regret. Office's oracle would be `2,089 B` smaller than the exact same-run v0.29 surface; Analytics would remain only `108 B` larger.

### Physical bytes

Office:

- current physical region: `6,434,597 B`;
- same-unit level-19 physical region: `5,949,878 B`;
- saving: **`484,719 B`**;
- pack count: `28`;
- raw pack bytes: `6,701,038 B`.

Analytics:

- current physical region: `7,094,571 B`;
- same-unit level-19 physical region: `6,134,114 B`;
- saving: **`960,457 B`**;
- pack count: `57`;
- raw pack bytes: `27,425,639 B`.

No pack boundary, relationship or decode unit changed in this experiment.

## Compression-only cost

Three same-process repetitions were taken per effort level and the median retained.

| Surface | L1 CPU | L19 CPU | CPU ratio | L1 wall | L19 wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Office | `0.00865 s` | `0.48420 s` | ~`56x` | `0.00865 s` | `0.48422 s` |
| Analytics | `0.04709 s` | `8.80763 s` | ~`187x` | `0.04710 s` | `8.80890 s` |

That extra effort is real and cannot be hidden. But it is still far below the full same-run frozen-v0.29 research-product construction cost:

- Office frozen v0.29: ~`23.64 s` CPU / `23.65 s` wall;
- Analytics frozen v0.29: ~`206.65 s` CPU / `206.67 s` wall.

The causal opportunity is therefore not “restore v0.29 search.” It is to buy high compression effort **only on already-proven physical units where its byte value justifies the added work**, preserving the much cheaper v0.30 discovery/geometry path.

## Current semantic/access invariants

The current materialized level-1 candidates used to define the raw units remained valid:

Office:

- max member amplification ~`4.00113x`;
- mean selective amplification ~`1.02037x`;
- max decode unit `524,288 B`;
- filesystem fidelity and tail recovery passed.

Analytics:

- max member amplification `1.0x`;
- max decode unit `524,288 B`;
- filesystem fidelity and tail recovery passed.

Because the level-19 result was not materialized into an archive, this oracle makes no new reader/recovery/integrity claim for those counterfactual bytes. Geometry is unchanged by construction, but product credit requires a real candidate and ordinary hostile/referee gates.

Process peak RSS during the hosted oracle was ~`474 MiB`. This is whole-process/harness peak memory, not a clean differential attribution to level 19, so it is preserved as a resource signal rather than claimed as a memory regression or win.

## Causal conclusion

The dominant Office/Analytics density debt is **not currently evidence for a representation/locality redesign**. With the existing physical units frozen, mature compression effort almost exactly reconstructs the v0.29 density floor.

That does **not** authorize globally switching v0.30 back to level 19. Such a move would deliberately surrender part of the creation-compute advantage that justified reactivating v0.30. The correct next question is how much of this counterfactual headroom the already-existing EG08/EG11 adaptive-effort machinery captures, what residual it misses, and why.

In particular, EG11 already carries an exact effort ladder `(3, 6, 12, 19)` over selected final-pack paths while preserving geometry. Before adding any new selector or effort rule, measure pack-by-pack:

- incumbent level-1 storage;
- all ladder sizes;
- EG11 stopping point / selected effort;
- full-level-19 oracle size;
- residual bytes left on the table;
- added CPU per recovered byte;
- RAW-incumbent promotion and hot/cold/ordinary-pack scope.

If residual headroom comes from non-monotonic ladders after EG11's first-regression stop, the next hypothesis should be a cheap continuation signal, not a broader pack geometry change. If EG11 already captures nearly all of the oracle, the next task is product/composition admission of that existing candidate rather than another mechanism.

## Preservation

- Frozen Genesis scores are unchanged: ONE `275,219,901 B`, v0.29 `137,499,525 B`, frozen v0.30 `150,055,575 B`.
- Frozen Genesis creation CPU remains ONE `3.0791 s`, v0.29 `806.5369 s`, v0.30 `33.0603 s`.
- `research/cmpct1` and all ONE evidence remain untouched and active as the secondary research line.
- No version/tag/release/locality/integrity/recovery/comparator rule changed.
- The counterfactual receives no aggregate/R4/release credit until implemented as a real candidate and composed under the repository's ordinary evidence gates.

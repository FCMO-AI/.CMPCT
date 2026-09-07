# ONE-G0.2 hierarchy first-level fusion result — 2026-09-06

Status: **terminal diagnostic FAIL; mechanism preserved as causal evidence, not promoted**.

## Authority

- Branch: `research/cmpct1`
- Result-bearing source: `316b1e0d22ca8895277a3efa5bd7eafb3e68313d`
- Workflow: `ONE-G0.2 hierarchy first-level fusion diagnostic`
- Run: `34072733919`
- Job: `101592955267`
- Preregistration: `docs/one/prereg/ONE_G02_HIERARCHY_FIRST_LEVEL_FUSION_PREREG_2026-09-06.md`

## Frozen result

Semantic byte parity passed on every frozen row. The candidate removed the full first-level `one_level_ref[segment_count]` staging array and retained only the much smaller parent level.

| row | seed transient | candidate transient | transient ratio | elapsed ratio |
| --- | ---: | ---: | ---: | ---: |
| hier-4097-ref | 163,960 B | 80 B | 0.000488x | 0.811774x |
| hier-4097-mixed | 163,960 B | 80 B | 0.000488x | 0.745081x |
| hier-16384-ref | 655,520 B | 160 B | 0.000244x | 0.800481x |
| hier-65536-mixed | 2,622,080 B | 640 B | 0.000244x | 0.806846x |

Median elapsed ratio = **0.803663x**. Every row was faster than seed and transient staging fell by ~99.95–99.98%, but the preregistered median gate required `<=0.80x`. The workflow therefore correctly failed.

## Decision

**FAIL the preregistered diagnostic.** Do not round, retune, weaken or reinterpret the `0.80x` threshold after seeing the result. Do not rescue this exact candidate with segment-count, corpus, density or Surprise-rate thresholds.

The result is nevertheless mechanism-level evidence: eliminating the first-level derived ref array is directionally valuable, but the candidate still performs an extra per-chunk span-summing pass over `Segment[]` before it can emit each concat header. The shared writer's mandatory validation pass already sums segment lengths into total coverage. A causally distinct follow-up may test whether the small set of hierarchy group spans can be captured during that required validation pass, eliminating the remaining pre-emission span reread without changing canonical bytes, acceptance semantics or reader behavior.

That follow-up is a new hypothesis and must have its own preregistration. It is not rehabilitation of this failed gate by changing its threshold.

## Strongest hostile interpretation

Hierarchy is a structural corner of the current writer, not the ordinary path. Even a future local PASS cannot claim system-wide throughput improvement without a full shared-writer A/B that charges validation, Surprise emission, hierarchy, roots, allocation and resource checks. The enormous nominal staging-byte reduction also must not be equated with RSS reduction without process-isolated measurement.

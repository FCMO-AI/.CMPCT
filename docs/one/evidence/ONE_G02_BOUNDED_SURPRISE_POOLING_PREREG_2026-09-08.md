# ONE-G0.2 — bounded Surprise pooling preregistration

Date: 2026-09-08
Baseline source: `b5fafaf54e24bcfd357aac1871a8b27855d9e6fd`
Experimental line: `ONE-G0.2`

## Mission Lock / Referee

The repaired native-writer stage-owner lane reached its 1 MiB scientific workload and failed during `Program.validate_shape()` with `OneError: node count exceeds declared limit`. The semantic/adjudication tests had already passed. This is therefore treated as a representation/resource falsifier, not CI plumbing and not permission to raise the hard node limit.

Causal hypothesis: the current compiler creates one reader-visible `surprise` node per Surprise fragment. On heavily fragmented but otherwise valid temporal plans, node count therefore scales with fragment count even though the useful information is simply bounded explicit Surprise bytes interleaved with generic ranges from the previous root.

### Falsifiable hypothesis

Contiguous, output-local Surprise fragments can be pooled into bounded `surprise` nodes and addressed by ordinary ranged `Ref`s, while preserving the existing generic ONE grammar and exact semantics. A node-budget-aware grouping rule should make the 1 MiB fragmented plan valid under the unchanged `Limits.max_nodes=4096` cap without increasing total Surprise payload bytes or materially worsening generic range-cone work.

### Disproof

Reject this repair if any required row:

1. exceeds the existing hard node/depth/output/work limits;
2. changes reconstructed bytes, root digests, or canonical decode semantics;
3. adds a reader-visible operation or temporal/version-specific reader mechanism;
4. increases total explicit Surprise payload bytes relative to the same segment plan;
5. causes the existing generic unauthenticated range executor to exceed 2.1x modeled materialization or work for a 4 KiB request on the targeted 1 MiB fragmented family; or
6. requires corpus-tuned thresholds rather than a rule derived from declared resource bounds.

A failure is negative evidence. Do not raise `max_nodes`, weaken the 2.1x cone gate, reduce the 1 MiB workload, or disable validation to manufacture a pass.

## Frozen builder rule

Use only existing generic `surprise` and `concat` nodes plus ranged `Ref`s.

The grouping budget is derived from the Program's declared node cap, not workload identity:

- reserve one node for the previous/source root and one for the final current-root concat;
- budget at most two nodes per output-local group in the worst case: one pooled Surprise node plus one group concat;
- therefore `max_groups = floor((max_nodes - 2) / 2)`;
- partition the target in output order into at most `max_groups` contiguous groups, splitting plan segments only when needed to respect the group span;
- pool only the Surprise bytes inside each group; source/reuse pieces remain ranged refs to node 0;
- a group containing one piece may point directly to that piece rather than creating a redundant concat;
- the final current root composes group refs with the ordinary generic concat operation.

This is selective Crystallization inside ONE's existing representation, not a fallback codec and not an opaque legacy opcode.

## Frozen evidence matrix

Primary hostile row:

- 1 MiB `fragmented_every96` temporal relation plan, because that is the row class that exposed the hard node-count failure in the stage-owner lane.

Semantic breadth:

- 4 KiB, 256 KiB and 1 MiB productive relation families used by the native writer profile;
- exact full reconstruction through ordinary canonical encode/decode + reference VM;
- exact 4 KiB range reconstruction at beginning, middle and end of the 1 MiB fragmented current root through `reconstruct_range_unverified`.

Required measurements:

- raw segment count;
- legacy per-fragment node count and whether it violates `max_nodes`;
- pooled node count and node-cap headroom;
- pooled group count and maximum pooled Surprise bytes per group;
- total Surprise payload bytes before vs after pooling;
- canonical wire bytes;
- full-reader work/materialized bytes;
- 4 KiB range-cone materialization/work amplification and nodes touched.

## Decision

`ADVANCE_BOUNDED_SURPRISE_POOLING` only if all frozen semantic/resource/access gates pass and the previously failing 1 MiB fragmented plan validates under the unchanged cap.

Otherwise `REJECT_BOUNDED_SURPRISE_POOLING` and preserve the failure. The native-writer stage-owner profiler remains blocked until a hard-cap-valid representation exists; it must not silently skip the hostile 1 MiB row.

## Claim boundary

This experiment repairs Program graph granularity for already-discovered temporal plans. It does not prove authenticated selective reads, arbitrary Law discovery, product writer speed, v0.29/v0.30 superiority, or a canonical format change. The range executor remains explicitly unauthenticated; wire indexing and selective integrity remain separate debt.
# v0.30 locality-derived r24 micro-pack mission — 2026-09-12

Status: **Mission Lock / research-only**.

Parent negative: `V030_R25_MEMBERSHIP_COMPLETE_ARTIFACT_NEGATIVE_2026-09-12.md`.

## Falsifiable hypothesis

The current r24 micro-pack encoder sorts eligible members by size, but closes groups using a fixed/global target. A stronger product mechanism is to derive each group's decoded-size ceiling directly from the frozen selective-read law:

```text
raw_group_bytes <= 8 * smallest_logical_member_bytes
```

Because candidates are size-sorted, the smallest member is the first member admitted to a new group. Independent storage is the always-feasible 1x fallback.

Hypothesis: this locality-derived grouping can make every emitted S_PACK <=8x for every member while preserving enough cross-file context that, after current compact-control and implicit-membership encoding, the complete authenticated artifact remains smaller than the locality-safe independent-file control on both Developer and Tiny Files.

This is a mechanism test, not a target-size sweep. The factor `8` comes only from the frozen product contract.

## Builder variants

On the same normalized deterministic Developer and Tiny-Files trees:

1. **current-release-r24 diagnostic** — current v0.30 r24 builder, measured but not treated as an eligible r25 baseline when its S_PACK audit fails;
2. **independent control** — identical r24 encoder except micro-packing disabled (`micro_pack_max_file=0`), giving 1x tiny-member representation locality;
3. **locality-derived packer** — identical r24 encoder except `_build_micro_packs` groups eligible content by the existing dominant-extension buckets and size order, and flushes before adding a member would make total raw group bytes exceed `8 * first_member_size`;
4. **locality-derived + C25CC01** — existing two-copy compact-control profile over variant 3;
5. **locality-derived + compact membership** — the earned file-index membership grammar over the exact same physical data span as variant 4.

Every emitted locality-derived group must contain at least two unique content roots; a singleton stays independent so S_PACK framing cannot masquerade as a locality win.

## Frozen gates

For both workloads:

- strong user tree exact for independent and locality-derived r24;
- every emitted locality-derived S_PACK has `decoded_pack_bytes / member_logical_bytes <= 8.0` for every member;
- max decoded S_PACK <= existing 8 MiB product ceiling;
- C25CC01 accepts the locality-derived artifact;
- compact-membership candidate reconstructs the exact mature r24 semantic index;
- candidate physical data span is byte-identical to the locality-derived C25CC01 source;
- primary-control corruption recovers through authenticated tail;
- candidate complete bytes are strictly smaller than **both** locality-derived C25CC01 and the independent r24 control; ties fail;
- no path, extension, benchmark identity or content hash is used to decide the group byte ceiling or candidate publication. Existing extension buckets are retained only as the mature Builder's pre-existing compression-context partition, not as the new admission law.

PASS: `LOCALITY_DERIVED_MICROPACK_EARNED`.

FAIL: `RETIRE_OR_REDESIGN_LOCALITY_DERIVED_MICROPACK`.

## Measurements

Record complete stored bytes for all variants, logical bytes, pack count/member count, max/weighted member amplification, max decode unit, control bytes, candidate savings, build CPU/wall, open/expand CPU/wall, strong verification and recovery. RSS remains diagnostic unless measured in isolated fresh processes.

## Promotion boundary

PASS would justify moving the derived pack ceiling into a product Builder candidate and then running the heterogeneous generalization/hostile suite. It does not authorize changing `docs/FORMAT.md`, versioning, public benchmark claims or ONE status.

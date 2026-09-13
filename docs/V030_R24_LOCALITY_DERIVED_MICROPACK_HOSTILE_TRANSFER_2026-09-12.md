# v0.30 locality-derived r24 micro-pack hostile transfer — 2026-09-12

Status: **Mission Lock / Hostile Reviewer / research-only**.

Parent evidence: `docs/V030_R24_LOCALITY_DERIVED_MICROPACK_MISSION_2026-09-12.md`.

## Earned seed

The exact-head hosted referee on `c2626cf3e03fadb9528e6acf86e98344dddf1e0f` earned `LOCALITY_DERIVED_MICROPACK_EARNED` on the deterministic Developer and Tiny-Files sources. The candidate was smaller than both the locality-derived C25CC01 control and the locality-safe independent-r24 fallback while preserving exact trees, authenticated tail recovery, hostile membership refusal and the frozen `<=8x` member-read law.

The mechanism under review is deliberately narrow:

```text
raw_group_bytes <= 8 * smallest_logical_member_bytes
```

Candidates are size-sorted inside the mature Builder's existing compression-context buckets. A singleton remains independent. The factor `8` is the frozen product locality law, not an empirical threshold.

## Falsifiable transfer hypothesis

The locality-derived ceiling is a general physical safety law, but **physical safety alone is not assumed to imply storage profitability**.

Hypothesis: across deterministic generator-distinct tiny-file populations, the derived packer will preserve exact trees and `<=8x` locality. Where cross-file context is useful, compact membership will beat independent storage; where it is not useful, the hostile evidence should expose the loss cleanly and force an exact economic admission/fallback layer rather than another pack-size threshold.

This test is intentionally allowed to falsify universal publication. A loss is useful evidence.

## Frozen hostile families

The referee generates all families locally with no workload-name or path identity in the candidate policy:

1. `balanced_structured_text` — many similarly sized structured text members with shared syntax but distinct values;
2. `skewed_structured_text` — a broad deterministic size distribution attacking the smallest-member-derived ceiling;
3. `incompressible_text_labeled` — deterministic pseudorandom bytes carrying text-like suffixes, attacking the mature extension context bucket and pack-compression economics;
4. `duplicate_forest` — repeated logical files plus a smaller set of unique text roots, attacking interaction with exact deduplication;
5. `singleton_buckets` — isolated eligible text members across distinct mature context buckets, requiring singleton fallback rather than forced S_PACK framing.

The corpus names and paths are diagnostic labels only. The candidate implementation remains the exact parent `LocalityDerivedBuilder`; no new selector sees those labels.

## Frozen measurements

For every family record:

- independent-r24 complete bytes;
- locality-derived-r24 complete bytes;
- derived+C25CC01 complete bytes;
- derived+compact-membership complete bytes;
- complete candidate delta versus independent and C25CC01;
- emitted group count and member count;
- max and weighted packed-member amplification;
- max decode unit;
- build CPU/wall for the physical variants;
- strong-tree exactness;
- candidate physical-payload identity versus the derived source;
- authenticated tail recovery and hostile membership refusal.

RSS is not claimed from this in-process diagnostic. Any promotion path must later measure isolated-process RSS.

## Verdicts

`LOCALITY_DERIVED_MICROPACK_GENERALIZES`
: all hostile families preserve correctness/locality and the compact-membership candidate is never larger than independent r24; at least one non-origin family emits a multi-member pack and is strictly smaller than independent.

`LOCALITY_DERIVED_MICROPACK_NEEDS_ECONOMIC_ADMISSION`
: correctness/locality remain intact but at least one hostile family is larger than independent r24. This is the expected trigger for a per-group or bounded-portfolio exact economic admission mechanism; it is **not** permission to tune the `8x` law.

`RETIRE_LOCALITY_DERIVED_MICROPACK_TRANSFER`
: any family violates exact-tree semantics, payload identity, recovery/hostile invariants, or `<=8x` locality. Such a result attacks the physical mechanism itself rather than merely its economics.

## Disallowed responses to a negative

- no widening `8x`;
- no file-extension/path/workload/hash dispatch;
- no removal of the losing hostile family;
- no threshold sweep over group sizes;
- no weakening of integrity, recovery, reader semantics or independent fallback;
- no release or format-version credit from this research lane.

If only economics fail, the next Builder must price **complete bytes** and fall back on ties/losses. Prefer proof/branch-and-bound that avoids building both candidates when a cheap bound is decisive, but first establish the exact economic oracle.

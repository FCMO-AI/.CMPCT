# v0.30 r24 locality-derived micro-pack Genesis15 transfer — 2026-09-12

Status: **Mission Lock / Referee / research-only**.

## Authority and claim boundary

This referee transfers the already-earned locality-derived micro-pack mechanism onto the exact 15 frozen physical workload identities used by the CMPCT1 / ONE Genesis gate:

- 10 `neutral_hostile_v1` rows;
- 5 `resemblance_hostile_v1` rows.

The frozen gate result remains untouched. This lane does **not** rerun or rescore ONE, v0.29, or the frozen v0.30 contender. It asks a narrower causal question: does the new physical grouping law remain safe and economically useful when applied across the exact same physical workload population?

Before any candidate build, every generated workload must match the frozen Genesis identity on:

- suite/name;
- file count;
- logical bytes;
- tree SHA-256.

Any mismatch makes the experiment invalid. A dependency/toolchain drift is not a product loss.

## Frozen mechanism

Physical groups are formed only inside the mature Builder's existing context buckets, ordered by size, under:

```text
sum(raw bytes in group) <= 8 * smallest logical member bytes
```

`8` is the frozen selective-read amplification law, not a fitted threshold. Singletons remain independent.

To avoid credit from asymmetric metadata, each workload compares:

1. independent r24 (`micro_pack_max_file = 0`) + `membership-v1`;
2. locality-derived r24 + the exact same `membership-v1`.

The decisive byte delta is `(2) - (1)`.

## Falsifiable hypothesis

Across all 15 exact Genesis workloads:

- every semantic/recovery/locality invariant remains true;
- a zero-group workload is byte-identical under the same grammar;
- every workload that emits groups is no larger under locality-derived grouping;
- byte-weighted aggregate same-grammar storage is strictly smaller than independent same-grammar storage.

A single grouped workload that grows is sufficient to require exact economic admission before any canonical integration. A locality/recovery/exactness failure attacks the mechanism itself.

## Required measurements

Per workload:

- same-grammar independent and locality-derived stored bytes;
- byte delta and percent delta;
- physical data-span delta;
- group/member counts;
- max and weighted packed-member amplification;
- max decode unit;
- independent/derived build CPU and wall;
- membership transform/open-expand CPU and wall;
- strong-tree exactness;
- authenticated tail recovery.

Aggregate:

- total logical bytes (must equal frozen `265,969,714 B`);
- total same-grammar bytes per physical strategy;
- total delta;
- count of grouped wins/ties/losses;
- worst locality amplification and largest decode unit;
- sums of diagnostic in-process build CPU/wall.

In-process timing is diagnostic only. No isolated RSS, release throughput, or canonical creation-speed claim is earned here.

## Verdicts

`GENESIS15_MICROPACK_GENERALIZES`
: exact corpus seal passes; all invariants pass; grouped rows never lose; zero-group rows tie; aggregate bytes strictly improve.

`GENESIS15_MICROPACK_NEEDS_ECONOMIC_ADMISSION`
: exact corpus seal and invariants pass, but one or more grouped rows grow or zero-group rows differ. Next step: exact complete-byte economic admission/fallback, not threshold tuning.

`RETIRE_GENESIS15_MICROPACK_TRANSFER`
: exactness, recovery, or `<=8x` locality fails after a valid corpus seal.

`INVALID_GENESIS15_INPUT_SEAL`
: any generated workload differs from frozen Genesis identity. This is infrastructure/input drift and receives no product verdict.

## Promotion boundary

Even `GENESIS15_MICROPACK_GENERALIZES` remains research-only. Canonical integration still owes the current v0.30 composed frontier, authenticated format integration, native parity where applicable, hostile malformed input, fresh-process CPU/wall/RSS, reader throughput, recovery and exact-head release CI.

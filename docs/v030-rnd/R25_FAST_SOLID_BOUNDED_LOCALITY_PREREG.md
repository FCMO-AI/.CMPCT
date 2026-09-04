# R25 compact inline-solid bounded-locality transfer — frozen preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Date frozen: 2026-09-03

Parent evidence: `docs/v030-rnd/R25_FAST_SOLID_INLINE_ORACLE_RESULT.md`

## Scientific question

The parent inline-solid v3 oracle found joint size+create headroom against both ZIP/Deflate-9 and solid tar+Zstd-19 on 6/15 hostile/resemblance workloads, but exported a serious product debt: one monolithic solid stream can require decoding far more than the selected member and has not paid strong member/integrity/index cost.

This experiment asks one question only:

> **Does any of that already-observed six-row headroom survive when the data stream is partitioned into deterministic independent decode units whose raw decoded context is <=8x every non-empty member in the unit, each unit is <=8 MiB raw, and exact member/unit integrity plus a deterministic access index are charged to the candidate bytes and create time?**

This is an R4 product-survival oracle, not a new Foundry thesis and not a release benchmark.

## Frozen corpus

Run only the six rows that were jointly viable in the parent v3 result:

1. `neutral_hostile_v1/07_incompressible_and_encrypted_like`
2. `neutral_hostile_v1/08_many_tiny_files`
3. `neutral_hostile_v1/10_large_mixed_binary`
4. `resemblance_hostile_v1/01_shifted_versions`
5. `resemblance_hostile_v1/02_false_neighbors`
6. `resemblance_hostile_v1/05_incompressible`

Source-tree identity must match the accepted v0.29 corpus identities used by the parent oracle. No workload identity may alter the format beyond selecting the already-observed parent winning layout/level tuple listed below.

## Frozen parent configurations

The experiment does **not** sweep codecs, levels, threads, or new orderings. It carries forward exactly the parent row's best jointly viable tuple:

- neutral/07: `inline-ext`, Zstd level 12, threads 0;
- neutral/08: `inline-path`, Zstd level 15, threads 0;
- neutral/10: `inline-ext`, Zstd level 6, threads 0;
- resemblance/01: `inline-path`, Zstd level 15, threads 0;
- resemblance/02: `inline-ext`, Zstd level 3, threads 0;
- resemblance/05: `inline-ext`, Zstd level 1, threads 0.

Changing one of those tuples after execution begins requires a superseding freeze.

## Frozen bounded-unit construction

Files are ordered by the carried parent layout. Units are formed greedily in that order. A file may join the current unit only when both conditions remain true:

1. total raw member bytes in the unit are <= `8 * min(nonzero member bytes in unit)`;
2. total raw member bytes in the unit are <= 8 MiB.

Zero-byte members form zero-payload entries and do not gift representation bytes; they may not be used to justify a positive decoded-context denominator.

Each unit payload is the exact concatenation of its members' raw bytes and is compressed as an independent Zstd frame at the frozen row level. This is deliberately a simple lower-complexity bounded-locality construction, not a production parser design.

## Charged representation facts

The archive must charge, in its measured bytes:

- an archive magic/version header;
- a deterministic access index;
- path reconstruction data;
- member unit/offset/length data;
- one SHA-256 identity for every member;
- unit raw length and compressed length;
- one SHA-256 identity for every unit;
- every compressed unit byte.

The decoder must reconstruct the full tree and verify all charged member/unit identities. No external path table, member hash, source length, unit boundary or discovery decision may be gifted.

## Timing boundary

Candidate `create_s` starts before reading member payloads and ends after archive publication. It includes:

- source/member scan;
- member SHA-256;
- deterministic unit construction;
- unit SHA-256;
- all Zstd compression;
- access-index serialization + SHA-256;
- archive write.

ZIP and tar+Zstd19 baselines use the same inherited competitor implementations and normalized source stage as the parent oracle.

## Locality accounting

For each non-empty member:

`decoded_context_amplification = unit_raw_bytes / member_raw_bytes`.

The row is locality-valid only if maximum amplification is <=8.0x and every unit is <=8 MiB raw. The deterministic uncompressed index is charged to archive bytes but is not entropy-decoded payload context; this is an explicit oracle boundary, not a release-locality receipt.

A later canonical Builder must still prove the repository's actual selective-read and decode-unit laws.

## Row-level survival rule

A row survives this transfer oracle only if **all** are true:

1. source tree identity is accepted;
2. full decoded tree is exact;
3. every member SHA-256 verifies;
4. every unit SHA-256 verifies;
5. maximum decoded-context amplification <=8.0x;
6. maximum raw unit <=8 MiB;
7. candidate archive is strictly smaller than ZIP;
8. candidate archive is strictly smaller than tar+Zstd19;
9. candidate create time is strictly faster than ZIP;
10. candidate create time is strictly faster than tar+Zstd19.

Ties lose. No aggregate win may hide a losing row.

## Decision vocabulary

This experiment is intentionally row-scoped rather than forcing an arbitrary global percentage threshold.

- `FAST_SOLID_BOUNDED_LOCALITY_ROW_SUPPORTED:<label>` — that exact structural row retains all parent joint headroom after the charged bounded-locality construction.
- `FAST_SOLID_BOUNDED_LOCALITY_ROW_NOT_SUPPORTED:<label>` — it does not.
- `CANDIDATE_INVALID` — construction/correctness/integrity/locality instrumentation failed and no scientific size/speed decision may be inferred for the affected row.

The family remains a conditional research candidate only for supported rows. Unsupported rows become scoped negative constraints.

## Oracle gift ledger

Gifted/deferred:

- perfect knowledge of which six parent rows to retest;
- perfect knowledge of each parent winning layout/level;
- no generic content-derived admission cost;
- no canonical r25 parser/native/platform implementation;
- no recovery/fuzz/hostile parser productization;
- no physical Android/platform execution.

Not gifted:

- representation bytes listed above;
- member/unit identities;
- exact reconstruction;
- source scan and candidate compression time;
- unit boundaries;
- <=8x raw decoded-context construction.

## Carrying-cost interpretation

A surviving row is still not automatically worth shipping. After this oracle, any Builder must price generic nomination/audition, permanent parser/native/platform surface, recovery/fuzz burden, and the fact that the parent mechanism failed 9/15 workloads. Small conditional byte wins may be insufficient to pay those global costs.

## Anti-sunk-cost rule

If no row survives, retire this compact-inline-solid family as a v0.30 product path; do not answer the loss with another codec-level/thread/layout sweep.

If only a narrow row survives, preserve it as a scoped opportunity and require a low-cost content-derived admission predicate before productization. If several structurally different rows survive, the next action is generic admission/canonical carrying-cost design, not more O0 codec tuning.

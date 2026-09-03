# R25 compact inline-solid bounded-locality transfer v2 — frozen preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Date frozen: 2026-09-03

Supersedes the unexecuted v1 freeze `R25_FAST_SOLID_BOUNDED_LOCALITY_PREREG.md`. v1 remains preserved. No result-bearing v1 execution occurred. The only change is explicit handling for a member larger than the unchanged 8 MiB decode-unit ceiling.

Parent evidence: `R25_FAST_SOLID_INLINE_ORACLE_RESULT.md`.

## Question

Does the parent inline-solid joint size/create win survive when representation bytes pay for a deterministic member index, member and unit SHA-256 identities, and independent Zstd units whose decoded payload context is <=8x each member and whose raw unit size is <=8 MiB?

This is an R4 product-survival oracle with zero release credit.

## Frozen rows and configurations

Only the six parent-supported rows are tested, using exactly their parent winning tuples:

- `neutral_hostile_v1/07_incompressible_and_encrypted_like`: `inline-ext`, level 12, threads 0;
- `neutral_hostile_v1/08_many_tiny_files`: `inline-path`, level 15, threads 0;
- `neutral_hostile_v1/10_large_mixed_binary`: `inline-ext`, level 6, threads 0;
- `resemblance_hostile_v1/01_shifted_versions`: `inline-path`, level 15, threads 0;
- `resemblance_hostile_v1/02_false_neighbors`: `inline-ext`, level 3, threads 0;
- `resemblance_hostile_v1/05_incompressible`: `inline-ext`, level 1, threads 0.

No codec/level/thread/layout sweep is allowed.

## Frozen unit grammar

Files use the carried parent order.

Members <=8 MiB are greedily co-located only while total raw unit bytes remain <=8 MiB and <=8 times the smallest non-empty member in that unit.

A member larger than 8 MiB is split into consecutive dedicated <=8 MiB raw segments. Its index entry records every segment. Reconstruction concatenates all charged segments and verifies one SHA-256 over the complete member. For such a member, total decoded payload context equals member bytes (1.0x).

Zero-byte members use indexed zero-payload entries.

Each non-empty unit is compressed as an independent Zstd frame. The archive charges: version header, deterministic index, prefix-delta paths, ordered member segment descriptors, member lengths, one member SHA-256 each, unit raw/compressed lengths, one unit SHA-256 each, and all compressed unit bytes. No required decoder fact is external.

## Timing and correctness

Candidate `create_s` begins before reading member payloads and ends after archive publication, including source scan, all member/unit hashes, unit construction, Zstd compression, index serialization/hash and write.

Full extraction must verify every unit and member identity and reproduce the accepted exact tree. ZIP and tar+Zstd19 use the inherited parent competitor implementations on the same normalized source.

## Locality

For each non-empty member:

`amplification = sum(raw bytes of units required for the member) / member raw bytes`.

A row must have maximum amplification <=8.0x and maximum raw unit <=8 MiB. The deterministic uncompressed index is charged to archive bytes but is not counted as entropy-decoded payload context; this remains an oracle boundary, not a release selective-read receipt.

## Row decision

A row is `FAST_SOLID_BOUNDED_LOCALITY_ROW_SUPPORTED:<label>` only if exact tree + member/unit integrity + <=8x + <=8 MiB all pass and the measured candidate is strictly smaller and strictly faster to create than both ZIP/Deflate-9 and tar+Zstd19. Ties lose.

Otherwise a valid measurement is `FAST_SOLID_BOUNDED_LOCALITY_ROW_NOT_SUPPORTED:<label>`. Construction or instrumentation failure is `CANDIDATE_INVALID` and earns no scientific size/speed conclusion for that row.

## Gift and carrying-cost ledger

Gifted: knowledge of the six parent rows and their winning configuration; generic admission; canonical r25 integration; recovery/fuzz/native/platform/physical-Android productization.

Not gifted: archive/control/index bytes, exact reconstruction, member/unit identities, source scan, compression time, unit boundaries, large-member segment descriptors or bounded decoded payload context.

A surviving row still must pay generic content-derived admission and permanent parser/native/platform/recovery cost before a Builder can be justified. If no rows survive, retire this family for v0.30 rather than tuning codec levels or competitor settings.
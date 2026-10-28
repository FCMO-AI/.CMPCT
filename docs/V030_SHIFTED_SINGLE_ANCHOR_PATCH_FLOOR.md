# v0.30 Shifted single-anchor native-patch payload floor

Status: **terminal negative evidence for this exact representation family**. Research only; grants no release credit and changes no product selector or grammar.

## Evidence binding

The decisive source is the completed exact GitHub Actions artifact `v030-shifted-zstd-base-patch-9938d8bfea479496ed63c00aec4237a28c3f95b1` from candidate SHA `9938d8bfea479496ed63c00aec4237a28c3f95b1`, artifact digest `sha256:49b6aadf25362e6ed53c7fa8f8ca6d0035e538aec9ca2bb23b98aa5908a970cd`.

Frozen target: `resemblance_hostile_v1/01_shifted_versions`.

Same-run solid Zstd-19 complete artifact: **1,694,674 B**.

Accepted v0.29 floor: **1,723,056 B**.

The base+patch oracle includes source scanning, anchor selection, native patch construction, framing, hashing and publication in creation time. Every arm reconstructed the exact tree and remained research-only.

## Optimistic payload-floor proof

For this grammar, before any path/integrity/framing bytes are charged, the irreducible encoded payload is:

`payload_floor = anchor_zstd19_bytes + sum(native_patch_blob_bytes)`

The source artifact reports one selected anchor compressed to **1,677,969 B**. The measured patch totals are:

| Patch level | Complete artifact | Patch blobs | Optimistic payload floor | Gap vs solid Zstd-19 | Complete create |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,701,847 B | 22,635 B | 1,700,604 B | +5,930 B | 0.301494 s |
| 3 | 1,728,987 B | 49,775 B | 1,727,744 B | +33,070 B | 0.370436 s |
| 6 | 1,701,341 B | 22,129 B | 1,700,098 B | +5,424 B | 0.566076 s |
| 9 | **1,701,269 B** | **22,057 B** | **1,700,026 B** | **+5,352 B** | 0.575731 s |

The best complete artifact is already **6,595 B larger** than solid Zstd-19. More importantly, even granting the representation an impossible **zero-byte cost for every path, integrity field, table and framing byte**, its best encoded payload is still **5,352 B larger** than the same-run solid Zstd-19 artifact.

Therefore no framing optimization, metadata shaving, path compaction, hash deduplication, serializer rewrite, or other R0-R3 change that leaves the single-Zstd-anchor + native-patch payload semantics unchanged can satisfy the strict Zstd size contract on this frozen target.

## Domination-rubric audit

- Strict target: every frozen row strictly smaller **and** faster to create than ZIP/Deflate and solid Zstd-19, while preserving accepted v0.29 and all CMPCT invariants.
- Diagnosis: **D4 — representation / physical-layout floor**.
- Minimum radicality: **R4**.
- Saturation: **S1** now applies to this exact single-anchor native-patch representation, in addition to the broader Shifted family's prior low-yield/retirement/exported-cost evidence.
- Referee / pre-mortem: the apparent +6,595 B miss might have been mostly framing debt, so further metadata work was inadmissible until payload ownership was isolated.
- Builder / decisive instrument: decompose the already-completed exact artifact into anchor payload, patch payload and all remaining framing, then gift the candidate zero framing cost.
- Hostile reviewer / post-mortem: this proof retires only the exact **single solid-Zstd anchor + native patch** grammar. It does **not** prove that multiple bases, content-defined shared dictionaries, bounded transform dictionaries, or another genuinely different reconstruction family cannot win.
- Measured gap change: complete miss **+6,595 B**; impossible-best payload miss **+5,352 B**.
- Decision: **RETIRE_FAMILY** for this exact grammar. Do not spend further deep-CI budget tuning patch levels or framing around it.

## Next decisive representation class

Any reopened Shifted R&D must change the bytes that constitute the payload floor itself. The next admissible R4 tests should compare genuinely different ownership/reconstruction classes—for example a bounded multi-base or content-defined shared-dictionary representation—while pricing source analysis, dictionary/base construction, patch generation, hashing, framing, publication, locality, decode units, recovery and platform burden inside the honest contract.

A new scalar threshold or compression level is not new evidence and does not reopen this family.

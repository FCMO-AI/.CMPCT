# v0.30 Shifted bounded multi-base patch — terminal negative

Status: **research family retired**. This document is negative evidence, not release authority.

Exact evidence source: `CMPCT v0.30 Shifted bounded multi-base patch oracle`, source commit `04d4b2f5c2cd52d1fbebf154cbcb007a1f10fc30`, artifact schema `cmpct-v030-shifted-multibase-patch-oracle-v1`.

The experiment changed the physical owner relative to the already-retired single-anchor patch grammar. It selected 2, 3, or 4 deterministic size-quantile bases and gave every other member an exact direct Zstd-19 fallback plus every locality-admissible `--patch-from` candidate. Candidate construction priced source observation, all direct compression, every patch attempt, SHA-256, framing, and publication. Every arm reconstructed the exact frozen Shifted tree and stayed below the 8x decoded-context locality ceiling.

Fresh external comparators on the same run were:

- ZIP/Deflate: **30,283,112 B**, **0.798695 s** creation.
- solid Zstd-19: **1,694,674 B**, **0.793940 s** creation.
- accepted v0.29 Shifted floor: **1,723,056 B**.

Measured arms:

| bases | complete bytes | create s | patch attempts | admitted patches | max context amp | gap vs Zstd-19 |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 3,378,253 | 3.185824 | 32 | 16 | 1.999995x | +1,683,579 B |
| 3 | 5,054,889 | 3.707752 | 45 | 15 | 1.999995x | +3,360,215 B |
| 4 | 6,731,432 | 3.637377 | 56 | 14 | 1.999995x | +5,036,758 B |

The two-base arm is already roughly **1.99x the solid-Zstd artifact** and **4.0x the solid-Zstd creation time**. Adding bases monotonically worsens complete size because full-base ownership costs dominate any patch benefit. This is not a framing or metadata near-miss.

## Domination audit

- Strict target: every frozen row strictly smaller and faster than ZIP/Deflate and solid Zstd-19, with accepted-v0.29 and all safety/locality/platform floors intact.
- Diagnosis: **D4 — representation/physical-layout floor**.
- Radicality: **R4**.
- Active saturation: **S1 + S3** when combined with the prior proven single-anchor payload floor and repeated whole-snapshot ownership failures.
- RPS of the decisive experiment: **91**.
- Strongest surviving self-critique: the result retires **whole-file base ownership**, not all cross-version shared-substructure representations. A content-defined shared owner can still exploit byte-shift resilience without paying for another full snapshot.
- Terminal decision: **RETIRE_FAMILY**.
- Next decisive test: content-defined bounded shared-chunk ownership with exact dedup, honest native boundary-scan cost, <=8 MiB chunks, <=8x member read amplification, and fresh ZIP/Zstd/v0.29 competitors.

Do not reopen this family by changing base count, patch level, or quantile placement alone. Reopening requires new evidence that changes the ownership-cost model itself.

# v0.30 Shifted global exact-CDC dedup — terminal negative

Status: **terminal negative for global exact content-defined-chunk ownership**. Research only; this grants zero release credit, changes no selector or canonical grammar, and weakens no threshold.

Exact evidence source: commit `7fc89d50e42015da4d4c42d014d427c19b3f3352`, workflow `CMPCT v0.30 Shifted CDC dedup capacity`, run `33424577247`, job `99594962666`, artifact `v030-shifted-cdc-dedup-7fc89d50e42015da4d4c42d014d427c19b3f3352` (artifact id `9770291095`, uploaded ZIP SHA-256 `1ad201364aa8ee1b7876e2533b1cf987074793049cef75367eb791fc7320a1d1`). The job bound checkout and evidence to the exact source commit, reconstructed the exact tree, enforced <=8 MiB decode units and <=8x locality, and uploaded the result only after the evidence assertions passed.

## Referee / pre-mortem

Whole-snapshot bases and simple PrefixGraph variants leave Shifted close to, but above, solid Zstd-19. The R4 hypothesis was that byte shifts were destroying reuse only because ownership remained file-shaped. A rolling content-defined boundary should resynchronize after insertions/deletions; exact global chunk ownership would then store repeated regions once and compress only unique bytes.

The decisive disproof criterion was representation capacity, not implementation speed: if the best complete CDC artifact could not close a material fraction of the shipping PrefixGraph/Zstd gap even after exact dedup, another nearby chunk-size sweep would be inadmissible.

## Builder / decisive instrument

Frozen staged source: **33,526,764 B**, 19 files. Same-run comparators and product floor:

- shipping PrefixGraph: **1,701,398 B**
- solid Zstd-19: **1,694,674 B**
- ZIP/Deflate: **30,283,112 B**

Four deterministic CDC mean sizes were tested. Every unique chunk was Zstd-19 compressed exactly once per arm; all source scanning, hashing, metadata/framing and reconstruction checks were priced by the oracle.

| Mean CDC | Unique raw | Deduplicated references | Complete artifact | Arm time | Gap vs Zstd-19 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 16 KiB | 14,400,734 B | 19,126,030 B | **13,008,632 B** | 11.373 s | **+11,313,958 B** |
| 32 KiB | 20,695,180 B | 12,831,584 B | 18,700,163 B | 11.859 s | +17,005,489 B |
| 64 KiB | 25,023,005 B | 8,503,759 B | 22,572,309 B | 11.804 s | +20,877,635 B |
| 128 KiB | 27,233,269 B | 6,293,495 B | 24,549,574 B | 12.031 s | +22,854,900 B |

The best 16 KiB arm removes **19,126,030 B (57.1%)** of raw duplicate references and reduces the bytes actually passed through Zstd to **42.95% of the source**. Yet its complete artifact is still **7.65x** the solid-Zstd artifact and **11,307,234 B larger than shipping PrefixGraph**. The four-arm search itself processes 2.605x source bytes through compression inputs and takes 65.46 s end-to-end.

This is not a framing near-miss. The loss is in the physical representation: independently compressing exact chunks destroys the long cross-chunk entropy context that solid Zstd and PrefixGraph exploit.

## Hostile reviewer / post-mortem

The result does **not** say that byte-shift-resilient boundaries are useless. It says that **exact ownership + independent chunk compression** is the wrong use of them. The strongest surviving alternative must change what a chunk owns or how it relates to other chunks: edit/copy relations, bounded referential grammar, or another representation that retains long-range context while remaining locality-bounded.

That distinction matters because the best arm demonstrates real structural reuse; it simply exports a much larger compression-context cost than the deduplication saves. Reopening this family with 8 KiB/12 KiB/24 KiB means, a different hash, or metadata shaving would be novelty theater unless new exact evidence changes that ownership-cost model.

## Domination audit

- Strict target: **15/15**, every frozen workload strictly smaller **and** faster to create than ZIP/Deflate and solid Zstd-19, ties fail, accepted-v0.29 and all release laws preserved.
- Diagnosis: **D4 — representation / physical ownership**.
- Minimum justified radicality: **R4**.
- Active saturation: **S2 + S3 + S4** inherited and reinforced.
- RPS of the decisive experiment: **96/100**.
- Measured gap change: **-11,307,234 B versus shipping PrefixGraph**; the candidate moves dramatically away from the strict frontier.
- Strongest surviving self-critique: exact CDC finds genuine reusable bytes, so a relation-aware grammar that preserves compression context remains untested by this result.
- Terminal decision: **RETIRE_FAMILY** for global exact-chunk ownership with independent Zstd payloads.
- Next decisive test: do not sweep chunk sizes. Advance a genuinely different R4 relation/ownership model, with an optimistic payload-floor check before productization and honest search/build/locality cost.

This negative must remain visible when future Shifted work is selected: exact CDC dedup is a solved dead end unless the ownership semantics themselves change.

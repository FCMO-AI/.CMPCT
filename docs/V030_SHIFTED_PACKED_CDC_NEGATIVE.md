# v0.30 Shifted packed-CDC terminal negative

Status: **terminal negative for bounded first-seen CDC dedup plus independently compressed shared packs**.

Exact evidence source: `58030ef30479ce1595c970dc76bc0fad981fb53e`, workflow `CMPCT v0.30 Shifted packed CDC shared store`, run `33407095270`. This note grants zero release credit and changes no v0.29, ZIP, Zstd, locality, integrity, recovery, native, Android, or release threshold.

## Referee / pre-mortem

The prior independent CDC store was an S1 representation-floor loss because independently compressing exact chunks destroyed the long-range resemblance that solid Zstd-19 exploited. This R4 follow-up changed the payload representation rather than tuning chunk size: exact content-defined chunks were deduplicated, retained in deterministic first-seen order, packed into bounded 1–2 MiB shared streams, and each pack was compressed as one entropy context.

The decisive question was whether restoring cross-chunk context inside a locality-bounded pack could pull the *payload itself* below solid Zstd-19. Framing was treated separately so a metadata miss could not be confused with a representation-floor miss.

## Builder / decisive instrument

Fresh exact comparator remains solid Zstd-19 at **1,694,674 B**. All four arms reconstructed the exact tree, beat ZIP on size and creation time, beat both ZIP and Zstd-19 on creation time, stayed below the 8 MiB decode-unit ceiling, and stayed within the <=8x locality law.

| Mean CDC | Pack | Zstd level | Complete artifact | Packed payload | Create | Max read amp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 KiB | 1 MiB | 3 | 24,088,012 B | 24,073,015 B | 0.2679 s | 3.752x |
| 64 KiB | 2 MiB | 3 | 17,715,648 B | 17,701,184 B | 0.2490 s | 6.567x |
| 64 KiB | 2 MiB | 9 | **17,682,011 B** | **17,667,547 B** | 0.2740 s | 6.567x |
| 128 KiB | 2 MiB | 3 | 19,651,661 B | 19,638,628 B | 0.2546 s | 5.461x |

The best complete arm therefore misses solid Zstd-19 by **15,987,337 B**. More importantly, gifting the representation zero bytes for every chunk table, file row, path, digest, count, header, index, and other framing field still leaves the best compressed payload **15,972,873 B above** the complete Zstd-19 competitor.

Packing recovered about **6.46 MB** versus the best independent-CDC complete artifact (24,141,568 B -> 17,682,011 B), proving that cross-chunk context was causally important. It did not come remotely close to the strict size floor.

## Hostile reviewer / post-mortem

Strongest surviving critique: this retires first-seen exact CDC ownership with bounded raw concatenation packs, not every content-defined transform. The experiment still treats each unique chunk as an owned raw substring and only restores entropy context locally. A genuinely different representation could encode *relationships* among chunks rather than merely concatenate them: dictionary-coupled residuals, ordered sequence grammar, base+delta chunk families, or another transform whose optimistic payload floor is computed before productization.

The locality trade is also visible: raising the pack to 2 MiB helps size substantially but already pushes worst-member read amplification to 6.57x. Simply increasing pack size toward solid-archive behavior has little legal headroom before the 8x ceiling and would still need to erase roughly 16 MB. That is not a credible continuation of this family.

## Domination audit

- Strict target: 15/15 frozen workloads, every row strictly smaller and faster than ZIP/Deflate and solid Zstd-19, with accepted-v0.29 and all release laws intact.
- Diagnosis: **D4**.
- Minimum justified radicality: **R4**.
- Saturation: **S1 + S3 + S4**.
- RPS of the tested structural red: **98/100**.
- Measured gap change: complete CDC improved from 24,141,568 B to 17,682,011 B, but still misses Zstd-19 by **15,987,337 B**; impossible-zero-framing payload misses by **15,972,873 B**.
- Strongest self-critique: relation-encoding/dictionary-coupled chunk transforms remain untested and are genuinely different R4 families.
- Terminal decision: **RETIRE_FAMILY**.
- Next decisive test: a bounded relation-encoding representation that retains CDC resynchronization but stores residual/reuse structure against a small deterministic shared basis, with an optimistic payload floor and dictionary/search construction cost measured before full canonical integration. It must fail closed on <=8x locality and <=8 MiB decode units.

Do not reopen this family by changing Zstd level, nearby CDC means, metadata encoding, or pack size unless new exact evidence invalidates the payload-floor proof above.

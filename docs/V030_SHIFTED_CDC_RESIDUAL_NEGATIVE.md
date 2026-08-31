# v0.30 Shifted CDC residual-relation terminal negative

Status: **terminal negative for bounded recent-predecessor XOR residuals over exact CDC chunks**.

Exact evidence source: `d854a5cacd58836f3013001c529b26597f36b29d`, workflow `CMPCT v0.30 Shifted CDC residual relations`, run `33407845546`, job `99540249123`. The exact evidence assertion, public-surface guard, CI-topology check, tree reconstruction, locality/decode bounds and artifact upload all completed green. This note grants zero release credit and changes no threshold.

## Referee / pre-mortem

The preceding packed-CDC family had restored some cross-chunk entropy context but retained a framing-free payload floor 15,972,873 B above solid Zstd-19. This R4 experiment changed the representation again: exact content-defined chunks could be encoded as bounded XOR residuals against a generic, content-derived recent predecessor rather than each owning raw bytes. Basis search was bounded, chains were capped at depth four, and a residual was admitted only when its compressed bytes plus basis-id cost beat direct compression of the same chunk.

The decisive question was whether relation encoding could make the *payload itself* competitive before spending time on canonical framing/productization.

## Builder / decisive instrument

Fresh comparator remained solid Zstd-19 at **1,694,674 B**. All four arms reconstructed the exact source tree and remained below both the <=8x locality and <=8 MiB decode-unit ceilings.

| Mean CDC | Basis window | Zstd level | Artifact | Payload | Create | Residual chunks | Max depth | Max read amp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 KiB | 16 | 1 | 9,734,037 B | 9,720,613 B | 1.2890 s | 175 | 4 | 3.526x |
| 64 KiB | 64 | 1 | 6,995,132 B | 6,981,768 B | 1.4011 s | 207 | 4 | 3.906x |
| 64 KiB | 64 | 3 | **6,985,574 B** | **6,972,210 B** | 1.4168 s | 207 | 4 | 3.906x |
| 128 KiB | 64 | 1 | 7,664,153 B | 7,652,170 B | 1.3860 s | 181 | 4 | 4.173x |

The best complete arm misses solid Zstd-19 by **5,290,900 B**. Even gifting every path, digest, index, header, chunk table and other framing byte away, the best compressed relation payload still misses by **5,277,536 B**.

Creation is also structurally red: all arms take roughly 1.29–1.42 s, slower than the exact ZIP and Zstd-19 comparators. The payload-floor proof is sufficient by itself to retire this exact family; the creation loss makes continued micro-optimization even less justified.

## Hostile reviewer / post-mortem

The strongest surviving critique is narrow and important: XOR of aligned raw bytes is a weak edit model. It expresses substitutions well but handles insertions, deletions, shifted regions and reusable subsequences poorly. The result therefore retires **bounded recent-predecessor XOR residuals**, not relation encoding as a whole.

A legitimate next R4 representation must encode edit/reuse structure itself—for example bounded copy/literal instruction streams, deterministic local sequence grammar, or another basis transform with a pre-productization optimistic payload floor. It must price basis/search construction honestly and preserve the locality/decode ceilings. Increasing the recent basis window, changing Zstd levels, or shaving framing is not enough to invalidate this floor.

## Domination audit

- Strict target: 15/15 frozen workloads, each strictly smaller and faster than ZIP/Deflate and solid Zstd-19, ties fail, accepted-v0.29 and every release law preserved.
- Diagnosis: **D4**.
- Minimum justified radicality: **R4**.
- Saturation: **S1 + S3 + S4**.
- RPS: **99/100**.
- Measured gap change: best complete artifact improved from packed CDC 17,682,011 B to 6,985,574 B, but remains **+5,290,900 B** over Zstd-19; impossible-zero-framing payload remains **+5,277,536 B**.
- Strongest self-critique: edit-aware relation grammars remain untested and are genuinely different from aligned XOR.
- Terminal decision: **RETIRE_FAMILY**.
- Next decisive test: bounded content-derived copy/literal or edit-aware relation encoding with an explicit payload lower-bound check before any canonical integration.

Do not reopen this exact XOR family with nearby parameter sweeps unless new exact evidence invalidates the payload-floor proof.

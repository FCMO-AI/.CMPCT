# v0.30 Shifted content-defined shared-store terminal negative

Status: **terminal negative for the measured exact content-defined chunk ownership grammar**.

This note preserves the exact R4 evidence produced at source head
`c9cc638beac3e62c97b2733a9333d6a03f73587c` by the `CMPCT v0.30 Shifted content-defined shared store`
authority. It grants zero release credit and does not change any v0.29, ZIP, Zstd, locality, integrity,
recovery, native, Android, or final-release requirement.

## Referee / pre-mortem

After whole-file PrefixGraph, single-anchor patching, multi-base whole-file patching, and cluster-owned
representations saturated, this experiment deliberately changed ownership semantics. It partitions bytes
using a bounded content-defined chunker, stores each unique chunk once, compresses each unique chunk
independently, and reconstructs every logical file from authenticated chunk references.

The decisive question was not merely whether the complete archive beats solid Zstd-19. It was whether
any miss is recoverable by reducing control/framing, or whether the compressed shared payload itself is
already above the competitor. The latter is an exact representation-floor failure for this grammar.

## Builder / decisive instrument

Fresh exact comparators on the frozen Shifted workload were:

- accepted v0.29: **1,723,056 B**
- ZIP/Deflate9: **30,283,112 B**, create **0.781303615 s**
- solid Zstd-19: **1,694,674 B**, create **0.673384068 s**

All measured CDC arms reconstructed the exact tree, had 1.0x maximum member read amplification, and kept
the maximum decode unit far below 8 MiB. Creation was also fast (~0.19 s), so the failure is not runtime.
It is representation size.

| Mean chunk | Level | Complete archive | Unique compressed payload | Framing/control | Payload gap vs Zstd-19 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 64 KiB | 1 | 24,141,568 B | **24,128,126 B** | 13,442 B | **+22,433,452 B** |
| 64 KiB | 3 | 24,144,216 B | 24,130,774 B | 13,442 B | +22,436,100 B |
| 128 KiB | 1 | 25,176,722 B | 25,164,655 B | 12,067 B | +23,469,981 B |

The best 64-KiB arm found 414 total chunk references and 268 unique chunks, eliminating 6,886,256 raw
bytes through exact deduplication. That sounds attractive until the actual competitor is priced: after
gifting this representation **zero bytes for every path, digest, table, index, count, and framing field**,
its compressed payload alone is still **14.238x the complete Zstd-19 archive**.

Therefore no metadata shave, compact index, hash deduplication, framing rewrite, or nearby chunk-size
adjustment can turn this exact independently-compressed CDC-store grammar into a strict Zstd size win.

## Hostile reviewer / post-mortem

Strongest surviving critique: this proof retires **independently compressed exact chunks with this ownership
model**, not content-defined transforms in general. A dictionary-coupled chunk codec, cross-chunk entropy
state, ordered shared sequence grammar, delta-coded chunk payloads, or another transform that preserves
cross-chunk resemblance could have a radically different payload floor. Those are new R4 representations,
not rehabilitations of this one.

That distinction matters because the experiment reveals why the family loses: exact dedup removes about
6.89 MB of repeated raw bytes, but independent chunk compression destroys the long-range/shared context
that solid Zstd exploits so effectively. The right next move must preserve or explicitly encode that
cross-region resemblance rather than tune the current chunker.

## Domination audit

- Strict target: 15/15 frozen workloads, every row strictly smaller and faster than ZIP/Deflate and solid
  Zstd-19 while preserving accepted v0.29 and every release law.
- Diagnosis: **D4**.
- Minimum justified radicality: **R4**.
- Saturation: **S1 + S3 + S4**.
- Research Priority Score of the tested structural red: **97/100**.
- Measured gap change: best complete CDC archive misses Zstd-19 by **22,446,894 B**; impossible-zero-framing
  payload floor still misses by **22,433,452 B**.
- Strongest self-critique: coupled/dictionary/sequence-aware CDC transforms remain untested and are genuinely
  different representation families.
- Terminal decision: **RETIRE_FAMILY**.
- Next decisive test: an R4 transform that retains cross-chunk resemblance while bounding random-access
  cost—for example a deterministic shared dictionary/sequence grammar with an exact optimistic payload
  floor computed before full productization. The experiment must price dictionary construction and all
  search work inside creation time and must fail closed on <=8x locality and <=8 MiB decode units.

Do not reopen this exact family via smaller metadata, alternate independent Zstd levels, or nearby mean
chunk sizes unless new exact evidence invalidates the payload floor above.

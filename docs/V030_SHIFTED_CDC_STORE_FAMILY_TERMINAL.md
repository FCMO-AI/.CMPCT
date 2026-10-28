# v0.30 Shifted CDC-store family terminal evidence

Status: terminal negative evidence for the tested CDC-store ownership family. This document grants no release credit and changes no production selector, format, workload, threshold, or benchmark identity policy.

## Strict target

The frozen Shifted workload must be strictly smaller and strictly faster to create than both ordinary ZIP/Deflate and solid Zstd-19, while preserving the accepted v0.29 floor, exact logical tree, <=8x member read amplification, <=8 MiB decode units, recovery/integrity/platform requirements, and content-agnostic production policy.

Solid Zstd-19 on the exact experiments below is 1,694,674 bytes. A representation whose optimistic payload floor is already above that value cannot be repaired by framing or metadata optimization.

## Referee / pre-mortem

The single-anchor patch and PrefixGraph families were already saturated. Content-defined chunking was justified as a distinct R4 hypothesis because it could, in principle, discover shifted common material without benchmark identity and could cap locality by ownership unit. Three increasingly strong variants were required to answer the main objections rather than declaring the first miss universal:

1. exact-deduplicated CDC chunks compressed independently;
2. the same content-defined ownership with bounded ordered pack context, addressing the loss of cross-chunk compressor context;
3. bounded recent-basis residual relations, addressing the inability of exact chunk equality to encode near-equal shifted material.

The decisive instrument for every variant was the same: exact reconstruction and locality first, then complete-artifact and optimistic payload-floor comparison to solid Zstd-19, with all candidate construction work charged.

## Builder evidence

### A. Independent content-defined shared store

Exact source head: `c9cc638beac3e62c97b2733a9333d6a03f73587c`.

The best measured arm used 64 KiB average chunks at level 1:

- complete artifact: 24,141,568 B;
- payload floor: 24,128,126 B;
- complete gap versus Zstd-19: +22,446,894 B;
- payload-floor gap versus Zstd-19: +22,433,452 B;
- exact raw deduplication still saved 6,886,256 B before compression;
- creation was about 0.195 s and therefore fast enough, but size was structurally noncompetitive;
- exact tree, locality and decode-unit constraints passed.

Decision for this representation: `RETIRE_FAMILY`.

### B. Packed CDC shared store

Exact source head: `58030ef30479ce1595c970dc76bc0fad981fb53e`.

This variant restored bounded cross-chunk compression context by packing ordered CDC material while keeping pack ownership within the <=8 MiB decode-unit law. The strongest measured arm was 64 KiB average chunks, 2 MiB packs, Zstd level 9:

- complete artifact: 17,682,011 B;
- packed payload floor: 17,667,547 B;
- complete gap versus Zstd-19: +15,987,337 B;
- payload-floor gap versus Zstd-19: +15,972,873 B;
- creation: about 0.276 s;
- maximum member read amplification: about 6.567x;
- exact tree and decode-unit constraints passed.

Packing recovered several megabytes versus independently compressed chunks, so the objection was real, but the impossible-best framing-free payload remained almost 16 MB above Zstd-19. No framing or metadata work can close that gap.

Decision for this representation: `RETIRE_FAMILY`.

### C. CDC residual relations

Exact source head: `d854a5cacd58836f3013001c529b26597f36b29d`.

This variant allowed bounded recent-basis residual relations rather than requiring exact chunk equality. It substantially improved the family again:

- best complete representation: about 6.99 MB;
- optimistic payload remained about +5.28 MB above solid Zstd-19;
- honest creation rose to about 1.4 s;
- exact tree, locality and decode-unit requirements remained satisfied.

The residual relation therefore answered another strong objection and still left a multi-megabyte payload-floor deficit while also losing the creation-time objective.

Decision for this representation: `RETIRE_FAMILY`.

## Hostile reviewer / post-mortem

These results do **not** prove that every possible content-defined transform is impossible. They do prove that the current CDC-store ownership family is saturated for Shifted under the tested progression from equality -> bounded packed context -> bounded recent-basis residuals.

The surviving objection is global relation structure: a transform that directly describes a long-range translation/permutation/shift relation could behave very differently from a store whose primary ownership units are CDC chunks, even when that store permits bounded residuals. That objection requires a different representation family, not a fourth CDC-store tuning pass.

The important negative is the payload floor, not merely complete framing. All three descendants retain floors far above Zstd-19 after increasingly generous relation/context mechanisms. Continuing with average-chunk, pack-size, compression-level, table, hash, or framing sweeps would violate the domination rubric's saturation rule.

## Domination audit

- diagnosis: `D4` structural red;
- minimum justified radicality: `R4`;
- saturation: `S1` on each measured representation floor and `S3` for the current CDC-store family after three meaningful descendants failed;
- Research Priority Score: remains high (>=80) because Shifted is a release-critical structural red, but the score now applies to a **new representation family**, not CDC-store tuning;
- measured gap progression: payload deficit improved from +22,433,452 B -> +15,972,873 B -> about +5.28 MB, yet never approached a viable Zstd crossing and eventually also lost creation economics;
- strongest surviving self-critique: bounded CDC ownership may be the wrong coordinate system for a globally shifted relation;
- terminal decision: `RETIRE_FAMILY` for the current CDC-store ownership family and `ESCALATE_RADICALITY` within R4 to a qualitatively different relation representation;
- next decisive test: first measure an optimistic payload floor for a content-agnostic global/bounded structural relation (for example a translation/permutation-aware base transform) before building full framing. If that floor does not cross Zstd-19, retire it immediately.

## Forbidden reopenings

Unless new exact evidence invalidates a premise above, do not spend release-critical time reopening:

- independently compressed CDC shared chunks;
- bounded packed CDC shared stores;
- bounded recent-basis CDC residual stores;
- metadata/framing optimization around any of those floors;
- chunk-size, pack-size, or compression-level sweeps whose representation ownership is otherwise unchanged.

Negative evidence is preserved so future work can move to a genuinely different structural hypothesis rather than rediscovering the same losses.

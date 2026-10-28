# v0.30 pathdict exact-audition economics — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `037676d596ce5513df51f1bce14973da9be20426`  
Hosted run: `34749390365`  
Artifact: `v030-pathdict-v12-037676d596ce5513df51f1bce14973da9be20426`  
Artifact id: `10315217635`  
Digest: `sha256:60e91d0b8e142e7720bd8b5bde85460aafc816358ad2251c88ce873b1ae5e296`

## Mission lock

No selector was changed. Every historical path-blind raw-dictionary audition still executed through the exact `ZSTD_compress_usingDict` path. The referee only recorded information available before/after that audition: raw size, already-computed normal-candidate size/ratio, exact dictionary-candidate size, and economic margin. No threshold receives product credit from this run.

## Result

All final archives remained byte-identical to the clean exact pathdict control. Across the five hard/hostile targets:

- exact dictionary auditions: **8,155**
- exact winners: **5,481 (67.21%)**
- non-winners: **2,674 (32.79%)**
- total gross saving earned by winners: **450,927 B**
- total loss that would be incurred by forcing all non-winners: **41,806 B**

Per surface:

| Surface | Calls | Wins | Win rate | Gross earned saving | Forced loss on non-winners |
| --- | ---: | ---: | ---: | ---: | ---: |
| Developer | 1,265 | 567 | 44.82% | 171,039 B | 11,168 B |
| Neutral incompressible/encrypted-like | 1,260 | 59 | 4.68% | 1,328 B | 18,070 B |
| Tiny Files | 4,950 | 4,256 | 85.98% | 217,560 B | 10,901 B |
| False neighbors | 600 | 599 | 99.83% | 61,000 B | 8 B |
| Hostile incompressible | 80 | 0 | 0% | 0 B | 1,659 B |

The normal-candidate ratio is informative but not sufficient by itself. Developer's candidates at normal ratio <=0.75 were all winners, while its near-1.0 region contained almost all losses. Incompressible controls live near 1.0 and mostly/entirely lose. Tiny Files also lives mostly near 1.0 yet wins heavily. Therefore a global ratio threshold would risk encoding corpus-specific behavior rather than the underlying mechanism.

## Interpretation

The residual 8,155-call hot path contains real avoidable proof traffic: 2,674 exact auditions produce no stored-byte benefit. But winners are not sparse overall, so the next gate must be both cheap and conservative. A promising mechanism-level oracle is the already-measured precompiled `ZSTD_CDict` path: it can evaluate all 8,155 candidates in ~0.32 s, but its frames must **never** be emitted under the exact historical representation contract. The correct next referee is classification only: compare `CDict_total < normal_total` against the exact raw-dictionary economic verdict, emit exact raw-dictionary bytes as before, and measure false negatives/positives. Zero false negatives is required before using the proxy to skip exact auditions.

This result does not change R4, Genesis, canonical r24, v0.29 release authority, or ONE's secondary status.

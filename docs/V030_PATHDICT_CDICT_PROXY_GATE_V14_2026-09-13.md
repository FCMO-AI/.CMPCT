# v0.30 pathdict exact CDict proxy gate v14 — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `f9523adae93155c303871d12acaa0e91d399aac9`  
Hosted run: `34749547821`  
Artifact: `v030-pathdict-v14-f9523adae93155c303871d12acaa0e91d399aac9`  
Artifact id: `10314838954`  
Digest: `sha256:4810cf2780e6d54c1fd699235593055547e9bfd1b2cb3f66405f42b67673e88c`

## Frozen mechanism

The rule was frozen directly from v13 with no threshold tuning:

1. reuse the already-computed normal candidate;
2. evaluate every eligible member once with the precompiled `ZSTD_CDict` proxy;
3. if `CDict_total >= normal_total`, reject dictionary work immediately;
4. otherwise run the historical exact `cmpct.codec.zcd` audition;
5. emit `CODEC_ZSTDDICT` only if that exact candidate still strictly beats normal;
6. never emit CDict bytes.

Final archive identity against the ungated exact pathdict control was mandatory.

## Result

All five hard/hostile targets were byte-identical to the exact pathdict control:

- proxy calls: **8,155**
- exact historical calls: **5,481**
- exact calls avoided: **2,674 (32.79%)**
- exact rejects after proxy admission: **0**
- final archive identity failures: **0/5**

Aggregate creation economics:

- clean independent+pathdict portfolio CPU: **17.0321 s**
- gated fused portfolio CPU: **14.7053 s** (**0.8634x**)
- clean portfolio wall: **17.4812 s**
- gated fused portfolio wall: **15.1445 s** (**0.8663x**)
- gated portfolio / one independent build CPU: **2.0550x**
- gated portfolio / one independent build wall: **2.0934x**

The gate therefore removes real proof traffic without changing a byte, but it does **not** close the creation debt against a single independent artifact.

Per-surface expensive-work accounting:

| Surface | Proxy calls | Exact calls | Proxy rejects | Proxy CPU | Exact CPU |
| --- | ---: | ---: | ---: | ---: | ---: |
| Developer | 1,265 | 567 | 698 | 0.0745 s | 0.5935 s |
| Neutral incompressible/encrypted | 1,260 | 59 | 1,201 | 0.0365 s | 0.0198 s |
| Tiny Files | 4,950 | 4,256 | 694 | 0.0646 s | **5.0873 s** |
| False neighbors | 600 | 599 | 1 | 0.1174 s | 0.3060 s |
| Hostile incompressible | 80 | 0 | 80 | 0.0355 s | 0 s |

Tiny Files now dominates the remaining exact-audition cost. This is causal evidence against spending the next cycle on global proxy tuning: most Tiny candidates are genuine dictionary winners, so skipping them would buy speed by giving back density.

## Interpretation and next gate

v14 earns mechanism credit as a byte-exact proof-traffic reduction. It does not receive product/release credit yet. The frozen rule must next transfer unchanged across all 15 current stable workloads, with exact archive identity required on every row. Only after that transfer should fresh-process CPU/wall/RSS and composition be considered.

This result does not alter Genesis, R4, canonical r24, v0.29 release authority, or ONE's secondary status.

# v0.30 pathdict CDict proxy attribution — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `bd8e9ae0c018a704668de6fe1bf3a4692161f55a`  
Hosted run: `34749440258`  
Artifact: `v030-pathdict-v13-bd8e9ae0c018a704668de6fe1bf3a4692161f55a`  
Artifact id: `10315112878`  
Digest: `sha256:b4dc40f2c3d87d2672140b1c9b9b70263917343c7694d08e49b14ad93317ea7f`

## Mission lock

The precompiled `ZSTD_CDict` candidate was used only as a cheap economic proxy. Its bytes were never emitted. Every candidate still received the historical exact `cmpct.codec.zcd` audition, and only exact raw-dictionary bytes could enter the archive. Final archive identity with the clean pathdict control was mandatory.

The proxy decision was preregistered without threshold tuning: `CDict_total < normal_total`, exactly mirroring the product's strict economic law.

## Result

Across all five hard/hostile targets:

- candidates: **8,155**
- exact raw-dictionary winners: **5,481**
- CDict proxy winners: **5,481**
- true positives: **5,481**
- true negatives: **2,674**
- false negatives: **0**
- false positives: **0**
- exact stored-byte saving lost under the proxy: **0 B**
- projected expensive exact auditions: **5,481**
- projected exact auditions avoided: **2,674 (32.79%)**
- all-proxy CDict CPU: **0.385 s**
- all exact-oracle CPU in this attribution run: **8.395 s**
- final archive identity failures: **0/5**

Per surface the proxy classified every candidate correctly: Developer 567/1,265 winners; neutral incompressible 59/1,260; Tiny Files 4,256/4,950; false neighbors 599/600; hostile incompressible 0/80.

The CDict and exact compressed sizes are not byte/size identical. Observed `CDict_size - exact_size` ranges included Developer **-10..+1006 B**, Tiny Files **-6..+4 B**, and false-neighbors **-1..+47 B**. Therefore the result does **not** rehabilitate CDict frames as the product representation. It says only that on this origin+hostile set the cheap compiled path preserves the strict economic sign of the exact decision.

This is consistent with Zstd's own API contract: `ZSTD_compress_usingDict` reloads the raw dictionary and has significant startup delay, while CDict digests the dictionary once for bulk processing. Zstd also documents that raw-dictionary compression may use parameters based on source size, explaining why exact bitstreams can differ even when the economic decision agrees.

## Next disproof

Build the frozen proxy gate with no new threshold: run CDict for every eligible candidate; run exact historical `zcd` only if the proxy strictly beats the already-computed normal candidate; emit only exact bytes; fallback to normal if the exact audition unexpectedly fails to win. Require byte-identical final archives against the clean pathdict control. Measure CDict CPU + admitted exact CPU + end-to-end portfolio CPU/wall. Then hold the rule fixed and expand hostile/current15 coverage before any product integration.

No Genesis/R4/release score changes are authorized by this attribution.

# v0.30 pathdict reusable-CCtx attribution — 2026-09-13

Status: **research evidence; no release credit**

Exact head: `f830a054f3f1f9ee89f17a6f9b4d92ba06421018`  
Hosted run: `34749188867`  
Artifact: `v030-pathdict-v11-id0-ff0-calls8155-cpu7.745-wall7.747-cs3.298-ws3.322-f830a054f3f1f9ee89f17a6f9b4d92ba06421018`  
Artifact digest: `sha256:3125ead0e145b18762a1e68c9d67305e6f00fd342b5f86185692f8b4ed538630`

## Mission lock

v10 showed that sticky raw-dictionary state with `ZSTD_compress2` retained the large speed signal but changed 3/5 final archives and 3,424/8,155 dictionary frames. v11 isolated context allocation from dictionary processing: it reused one `ZSTD_CCtx` while continuing to call the exact `ZSTD_compress_usingDict(..., raw_dictionary, level=12)` primitive used by `cmpct.codec.zcd` for every audition. Every produced frame was compared byte-for-byte with `zcd`.

## Result

- dictionary calls: **8,155**
- frame identity failures: **0**
- final archive identity failures: **0/5**
- measured reused-CCtx dictionary encode CPU: **7.745 s**
- measured reused-CCtx dictionary encode wall: **7.747 s**
- fused portfolio / single-independent CPU ratio: **3.298x**
- fused portfolio / single-independent wall ratio: **3.322x**

The route is exact but does not remove the creation debt. Context allocation/free is therefore not the dominant owner. The expensive work is the raw dictionary processing performed by `ZSTD_compress_usingDict` on each frame.

## Consequence

Do not continue permuting CCtx lifetime under the exact historical bitstream contract. The next productive questions are:

1. how many of the 8,155 dictionary auditions ever win, and how concentrated is their stored-byte reward? A cheap admission/proof gate may avoid most raw-dictionary work while keeping the historical frame bytes for accepted members; or
2. if a precompiled `ZSTD_CDict` representation is reconsidered, preregister it as a **new representation-equivalence experiment**, not as an exact-bitstream optimization. It must repay from zero: deterministic bytes, same/lower stored bytes, exact logical reconstruction, authenticated integrity/recovery, selective access, hostile/resource bounds, native/platform decode parity, creation CPU/wall/RSS, and no semantic weakening.

v9/v10 remain negative evidence under their original exact-identity gates. This result does not retroactively promote them or alter Genesis/R4/release authority.

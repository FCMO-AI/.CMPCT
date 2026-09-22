# v0.30 pathdict Zstd context-reuse negative — 2026-09-13

Status: research evidence; no release credit.

v9 (`ZSTD_CDict`) and v10 (sticky raw dictionary + `ZSTD_compress2`) both retain the large dictionary-encode speed signal but fail the preregistered byte-identity gate against the existing `cmpct.codec.zcd` representation. v10 hosted run `34749002000` on `70b6c3d801d3caa4ecc4f70c874fdbaa5cb13c39` executed 8,155 dictionary calls, found 3/5 final archive identity failures and 3,424 frame mismatches, with measured sticky encode CPU/wall about 0.500/0.498 s. Therefore neither alternative receives product/promotion credit.

Next falsifier: reuse only the `ZSTD_CCtx` while continuing to invoke the exact raw-dictionary `ZSTD_compress_usingDict` primitive used by `cmpct.codec.zcd`. If exactness holds but encode time remains near the older ~7.8 s path, repeated dictionary processing—not CCtx allocation—is the owner. Do not relax identity retroactively.

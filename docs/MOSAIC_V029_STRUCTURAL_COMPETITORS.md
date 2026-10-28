# CMPCT v0.29 structural-competitor tranche

Status: **launched after deterministic inherited-frontier generalization passed; no v0.29.0 claim yet**  
Candidate: attempt #5 Mosaic Placement + Residual Program Packing  
Canonical on-disk revision: **24 unchanged**

## Generalization gate that unlocked this tranche

The portable 15-workload inherited-frontier run passed every preregistered requirement on source commit
`46604dc4a6daf31a840ecfc7bff99e79c8bf68ba` (workflow run `31990706195`). Its evidence is preserved as
`benchmarks/history/2026-08-17-mosaic-v029-generalization-v2.json`.

- exact repaired v0.28 frontier: **137,556,533 B**;
- attempt #5 portfolio: **137,507,932 B**;
- improvement: **48,601 B (0.03533%)**;
- workloads improved / regressed: **2 / 0**;
- aggregate creation ratio versus embedded v0.28: **2.1953x**, below the frozen **3.0x** ceiling;
- median workload creation ratio: **2.0391x**;
- maximum additional residual-program read amplification: **0.06774x**;
- baseline tree / byte drift rows: **0 / 0**;
- full regression suite and public-surface guard: **green**.

The two old-frontier gains are residual-program wins rather than favorable Mosaic-only synthetic cases:
`01_shifted_versions` saves **38,532 B** and `03_boundary_churn` saves **10,069 B**. The narrow single-file
scheduler reject fires exactly once on `10_large_mixed_binary`, removing a measured dead-end audition while
leaving accepted multi-file research paths unchanged.

Evidence provenance: Actions artifact `9275509158`, artifact ZIP SHA-256
`34e6d14cdbf14ae01d9dd4cb2d214f7096285d74034ea2967d07ce419a658523`; raw benchmark JSON SHA-256
`ca14e00f5080cf473a22db14ac6803c0635c9be52f451ebe243736a458c29fe3`.

## Structural competitor contract

The next gate archives each complete public deterministic suite once and compares attempt #5 to the exact
embedded v0.28 artifact from the same tree, then records structural competitors when their executables are
available:

- ZIP / Deflate-9;
- solid tar + Zstd-19;
- 7z / LZMA2;
- ZPAQ method 5;
- DwarFS;
- Borg repository snapshot.

The neutral aggregate receives the proven repair-v3 normalization **before every tool sees it**. Tool paths,
version output, creation time, bytes and semantic boundaries remain in the evidence record. Missing tools are
reported as unavailable; availability is not allowed to become a release-quality pass/fail shortcut.

### Hard CMPCT-side requirements

- attempt #5 must be **<= exact v0.28 bytes on both aggregate suites**;
- both selected artifacts must strong-verify;
- Mosaic descriptor read amplification must remain **<=8x**;
- extra residual-program read amplification must remain **<=2x**;
- full repository tests and the public disclosure/surface guard remain green.

There is deliberately no hard assertion that CMPCT must beat every competitor with different access/recovery
semantics. Any future wording such as “smaller than 7z” or “beats solid tar+Zstd” is valid only for a measured
aggregate where the evidence actually supports it.

## What a green structural sweep earns

A green result earns a **v0.29 canonical-release proposal**, not a merge or version bump. Reader-visible
Mosaic/Residual descriptors cannot be smuggled into canonical revision 24. Promotion must advance the format
revision and native reader together, with independent golden/malformed/resource vectors, authenticated-tail
recovery parity, portability/ZIP/platform surfaces, fresh release-performance evidence, and public docs/site
updated from durable measurements.

> Footnote: numeric version scarcity remains in force. Research bytes can be excellent and still fail release
> quality if the reader, recovery, native, portability or evidence surfaces are incomplete.

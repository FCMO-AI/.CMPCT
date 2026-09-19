# Frozen v0.30 RSS phase attribution result

**Status:** PRODUCT-SIDE RESOURCE DEBT CONFIRMED  
**Frozen product:** `f4b158a55a08b9b18b50e4e4abe4b9251048c772`  
**Harness head:** `2e5ad35d62447e1efd948b10b280b6d308d3ddc1`  
**Hosted run:** `34635700763` — SUCCESS  
**Artifact:** `10278960826`, digest `sha256:20e29c201fe279e6aa7fe68be6a260a422355993b452e040cecc986be42934e0`  
**Product/release credit:** none

## Question

Genesis reported high process-lifetime `ru_maxrss` for the frozen v0.30 comparator. Because `ru_maxrss` is monotonic, it can include Python/runtime/import state that existed before product work. The falsifiable question was whether the apparent resource debt was mostly harness/import accounting or whether the frozen product itself materially raised peak RSS during build.

The diagnostic executes the exact frozen product in a fresh child process, removes the current checkout from `PYTHONPATH`, source-seals all loaded `cmpct` modules to the frozen checkout, and measures current/high-water RSS at interpreter baseline, after product import, after build and after strong verification.

## Results

### Analytics/database

- archive: `10,392,498 B`;
- interpreter current RSS: `14,249,984 B`;
- after frozen-product import: `31,723,520 B`;
- import current increment: **17,473,536 B**;
- post-import HWM: `31,723,520 B`;
- post-build HWM: `178,909,184 B`;
- **build HWM increment above import: 147,185,664 B (~140.37 MiB)**;
- after-build current RSS remained `144,982,016 B`.

### Incompressible/encrypted-like

- archive: `10,220,425 B`;
- interpreter current RSS: `14,368,768 B`;
- after frozen-product import: `30,699,520 B`;
- import current increment: **16,330,752 B**;
- post-import HWM: `30,699,520 B`;
- post-build HWM: `140,255,232 B`;
- **build HWM increment above import: 109,555,712 B (~104.48 MiB)**;
- after-build current RSS was `98,869,248 B`.

Strong verification did not raise the HWM beyond the build peak in either case.

## Interpretation

The accounting concern was legitimate but does not remove the resource debt. Imports/runtime explain only about 16–17 MB of current RSS above interpreter baseline in these fresh children. The build itself raises the process high-water mark another roughly 110–147 MB.

Therefore:

> The high hosted-process RSS observed around Genesis is materially product-owned for the frozen v0.30 build path. Do not classify it as a harness artifact.

The result does **not** yet identify the owner inside the product. It is compatible with transient full-file buffers, compressor workspaces, candidate materialization, portfolio branches, Python object graphs or combinations thereof. The large difference between post-build HWM and current RSS, especially on incompressible input, suggests a substantial transient allocation component.

## Next resource experiment

Do not optimize blindly. Instrument the strongest current v0.30 build path at mechanism boundaries and attribute peak/current RSS around:

1. source enumeration / metadata collection;
2. candidate observation and transform materialization;
3. backend compression/workspaces;
4. selector/portfolio candidate retention;
5. archive assembly/index/integrity construction.

Prefer fresh-process phase isolation or child-per-mechanism experiments because one-process HWM cannot tell which later phase owns an earlier peak. Pair RSS with bytes materialized/candidate counts so fixes target memory traffic rather than merely Python object count.

This debt is independent of the current Office content-ZIP discovery seed and the Analytics tabular-co-lift seed. New mechanisms must not worsen it materially without compensating evidence.

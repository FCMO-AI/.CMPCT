# O2 outcome — direct Deflate export across a live-mmap mutation boundary

Date: 2026-10-23
Evidence class: **scientific correctness negative in a real installed-product path**, not a product fix or released regression.
Preregistration: `benchmarks/history/2026-10-23-v031-direct-deflate-mutable-source-o2-prereg.md`, frozen at commit `c79bfc222f94f8e5558cca199b3e7f88ff11153b`.
Executable: `benchmarks/v031_deflate_mmap_mutation_o2_court.py`.
Tested exact source: `45a5fd7bbe389a069f9253199346efa854c3d703` (original PR #284 Reader blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`; PR #284 owner source not modified here).
Hosted result: [GitHub Actions run 40020949922](https://github.com/FCMO-AI/.CMPCT/actions/runs/40020949922), job `120645057149`, **SUCCESS**.
Artifact: `12529628942`, `sha256:a9ab85e91e3d8ee84cbfe1bd7da718250e3a4429588412862a7ae7acdbd63e86` (includes original JSON, exact source SHA, Reader/oracle/prereg Git blobs).

## Direct observations (product-path reproduction)

| Case | Export call | Independent Python ZIP read | Outcome |
|---|---|---|---|
| Immutable original | returns successfully | accepted, original logical bytes | valid control |
| One physical Deflate byte modified *before* preflight | rejected | pre-existing target bytes preserved | intended static PR #284 protection confirmed |
| One physical Deflate byte modified *after* successful original preflight, one member | returns successfully | rejects member (`BadZipFile`) | **TOCTOU contradiction reproduced** |
| Same post-preflight mutation, three logical aliases reusing one physical blob | returns successfully | rejects all 3 members (`BadZipFile`) | **alias amplification reproduced** |

The deterministic hook delegates to the unmodified original `_verify_direct_deflate_blob`, then changes one byte through a **second writable file handle**, after verification returns and before ordinary ZIP construction. It asserts the same Reader's file-backed mmap sees that byte. A level-0 RFC1951 stored block preserves Deflate grammar, physical compressed size and logical output length while changing one logical byte. Independent `zlib.decompress(-15)` succeeds on the mutated stream; `zipfile` rejects because the ZIP records continue to carry the old CRC. The source physical payload is mutable even though this Reader's mapping is read-only.

Result does **not** refute PR #284's static corruption fix. It narrows its correctness claim to a stable archive-source epoch (or an equivalent enforced ownership/snapshot boundary). The validator observed valid bytes at one time and the exporter copied different bytes later. Read-only mmap is not a historical snapshot.

## What this does not prove

- A source that *cannot be modified* concurrently remains outside this failure mode; immutable-source operation is not refuted.
- A hostile actor rewriting every SHA/CRC/index commitment is a different authenticity model.
- Cross-platform mmap visibility, arbitrary mutation races, compressed-codec combinations, non-Deflate members, completed output durability, and performance are unmeasured.
- This is a reproducible **correctness negative** under a concurrent-source condition, not a benchmark, general vulnerability severity, or release-gate finding.
- No product code, tests, comparator, format, frozen releases or thresholds were changed.

## Causal alternatives and cheapest next discriminator

A post-copy `stat` or pathname recheck cannot provide full race exclusion: the source could change and revert between observations. The most robust bounded direction is to authenticate the **exact bytes staged for publication**, not merely an earlier view of the source: stream each physically copied Deflate payload into a private same-filesystem staging ZIP, hash/decompress the staged output against committed logical SHA/CRC and length, then publish atomically **only after** successful validation. A genuine immutable-source owner/snapshot contract is the simpler alternative if it can be enforced.

Either route requires explicit CPU/decode, output-sized staging, temp I/O/RSS and failure-cleanup accounting; alias deduplication cannot assume that a previously checked mutable physical blob remains unchanged on later copies. The next **cheap** discriminator is one independent staged-output oracle with the identical deterministic mutation, verified on actual emitted ZIP bytes, before rewriting the owner exporter.

## Counterfactual and coordination

A deterministic mutation precisely between `_verify_direct_deflate_blob` and `_direct_deflate_stream` reveals this guarantee boundary in seconds, whereas random concurrent writer stress could miss it. The test is useful whenever verification and publication read a mutable source in separate epochs. This is a prospective useful check, not yet repeated evidence for changing global discovery doctrine.

PR #284 owns the actual repair and cost decisions. This branch is isolated research and should be closed/retired when integrated into owner acceptance evidence. `docs/discovery/STATE.json` is untouched (concurrent PR #240 owns its reconciliation). No release and no merge from this scientific result alone.

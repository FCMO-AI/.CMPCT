# J24B03 — Direct-blob declared-size and physical-owner custody (prospective)

Date: 2026-10-27 UTC
Status: PREREGISTERED BEFORE IMPLEMENTATION
Authority: CMPCT released `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, r24).
Scientific precursors: J24B01/B02 PR #604, issue #605; source ownership J24C02 PR #569. Never overwrite their branches or historical expected failures.

## Observed baseline / invariant

Independent Builder-free, signed-index r24 evidence at #604 shows one physical RAW owner (128 B) with logical row declaring 136 B. Authentic primary/tail index hashes and unchanged blob SHA/CRC permit `preflight_archive` to accept the contradiction, direct RAW `read_range(128,8)` to return authenticated tail-index bytes, and `K_SYMLINK` full `read`/`verify` to accept the contradiction. `K_FILE` full read rejects via length check. The structural invariant is exact logical row length equals referenced physical uncompressed size for **direct S_BLOB regular files and symlinks**; this must hold independently of the requested slice, codec, declared member hash or writer provenance.

## Question, design and kill conditions

Can a constant-time, same-index size check in `validation._validate_storage`, plus a narrowly scoped Python Reader check covering `K_SYMLINK read`, `S_BLOB read_range` and the RAW BHDR/frame before mmap slicing, reject all authenticated size contradictions without changing bytes, normal valid behavior or revision-24 layout?

Compare: released Python Reader (historical negative); strict preflight; corrected Reader on identical constructed wire images; full read, explicit verify, zero/middle/tail ranges. A standalone range-length check is insufficient (zero-range admits invalid metadata); checking only K_FILE misses K_SYMLINK; calling `preflight_archive` separately on pathname for every range introduces an unrelated inode/TOCTOU boundary; changing SHA tier does not correct geometry. The simpler-control proposal is equality with already decoded immutable logical blob-table `usize` plus raw physical BHDR fields (no extra full-file hash).

**Prospective expected outcome:** valid 128/128 K_FILE and K_SYMLINK accept all exact reads/ranges; malformed 136/128, 120/128, zero/128, and positive 1/0 logical-owner cases reject preflight and ordinary read/range (including zero-byte range) regardless of whether requested bytes would have been inside the physical payload. RAW, Zstd, Deflate ownership where valid; invalid physical BHDR length/codec must never escape through the RAW fast slice. Independent historical #604 results stay unchanged and linked, not rewritten.

**Kill/rollback:** failure to reject any constructed authenticated contradiction; any mismatch on valid fixed-wire vectors; nonconstant metadata-only work for select ranges; false rejection of valid symlink target bytes; unintended changes in Builder/wire/index representation; inherited full Reader correctness or portability gates failing; confirmed substantial read hot-path cost without a stronger policy boundary. No merge or release from this narrow science; compose with #569 before any product promotion.

## Measurement / hostile controls / limits

Primary evidence rung: deterministic Builder-independent r24 wire images with unchanged physical SHA/CRC, independently recomputed primary and tail index commitment; compare historical vulnerable installed Reader to patched installed Reader. Verify both kinds, 3 codecs, logical over/under sizes, exact EOF, nonzero offsets, empty queries, physical-tail context, and `verify()`. Measure repeated direct range operation cost on identical valid images with source-exact code and separated process/import if achievable; avoid overinterpreting noisy timings. Inspect structural bounds for malformed physical BHDR lengths, but do not claim universal hostile parser completeness.

Cost ledger: archive bytes 0 change; create unchanged; extra O(1) comparisons on preflight and direct selected/full access; decode and whole-file SHA work unchanged except previously malformed symlink rejection. Product parity, CI across hosts, and exact full memory/performance gates remain separate and unmeasured until hosted receipts.

## Concurrency

Only isolated branch `agent/phased3-v031-j24b03-direct-blob-size-guard-20261027` on released main; do not edit #569, #604, #601. Announce to issue #605 and coordinate result to Reader owner. Preserve negative J24B01 preregistration as an independent falsified prediction. Do not edit discovery state, frozen benchmark, core version, release law or format revision.

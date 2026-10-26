# O195 — Authentic 4 GiB sparse r24 ZIP64 range A/B preregistration

**Preregistered before implementation/hosted result.** Date: 2026-10-26 UTC. Base is unreleased O193 PR #521 at `392112ce859db5a7f85be593c82d1cabc1f5131f`; no released CMPCT behavior is modified. This question extends O194 issue #522, whose source-shaped micro/physical input evidence is strictly lower-rung.

## Decision question and prediction

Does the `S_SPARSE` full-extent rescan for every `read_range` call cause *material end-to-end* overhead when a genuine 4 GiB sparse r24 archive is exported by an **independently installed** O193 Reader through actual ZIP64? O194 derived `E × Q` visits and constructed a 4 GiB / 4,096 physical-extent filesystem input. It did not run Builder, Reader or ZIP64. This test must not promote an optimization from the micro evidence.

**Prospective hypothesis:** On Ubuntu Linux with `SEEK_DATA/SEEK_HOLE`, a 4 GiB logical file formed from 4,096 isolated 4 KiB physical extents at 1 MiB offsets is emitted by the genuine Builder as `S_SPARSE` with many ordered disjoint extents. The O193 original Reader sees approximately 4,096 range calls, each scanning all extents. An experimental **out-of-tree** bisect-indexed reader adapter skips nonintersecting extents while producing identical range bytes and a byte-identical ordinary, stdlib-decodable ZIP64 export. Index construction/memory is charged; measured overall speedup is not assumed. Improvement is *material* only if repeated same-archive end-to-end export shows >5% robust wall reduction, without source, ZIP, CRC, SHA, memory or semantic regression. <3%, contradictory or noisy end-to-end improvement should retire index optimization as a current product priority even if metadata microbenchmark improves dramatically.

## Alternatives / cost model / controls

1. Keep the simple baseline. It may win if zlib/4 GiB hashing and writes dominate.
2. Early-break control: O194 showed it is ineffective in the suffix-hole regime; not repeated.
3. Per-reader/per-file sorted index with bisect: only valid after validating monotonic offsets, nonoverlap, positive lengths, bounds and physical decoded chunk-length consistency; rejected malformed metadata must *not* be silently reinterpreted. This is a temporary external adapter, **not** a product implementation.
4. Monotone read cursor can attain `O(E+Q)` under sequential-only access, but general `read_range` allows random access and rewind, making bisect an honest general control. Not implemented unless bisect changes the decision.

Track complete CMPCT and ZIP stored bytes, source allocation, number of real extents, source archive SHA, decoded ZIP SHA/CRC and ZIP64 identity, Builder create wall/CPU, reader open, full export CPU/wall, range work wall/calls/bytes, incremental index build wall and Python object bytes, peak process RSS, and temporary files. Use same source archive/Reader/process, A-B-B-A runs; display raw runs and medians, do not claim identical cold-cache behavior or official release speed. Direct index-built baseline output must remain binary-identical to indexed output. Stdlib ZIP independent consumer streams the full 4 GiB without materialization, and source SHA is independently streamed. Negative control mutates the observed extent order and requires index validation to reject it.

## Kill/stop criteria

- Builder does not choose `S_SPARSE` or physical host does not supply sufficient disjoint extents: **not product-validating**, report host/Builder limitation and do not fabricate the result.
- Exact-head installed source identity fails: no performance claim.
- Independent ZIP reader detects any byte/CRC/size/name mismatch or source CMPCT changes: **FAIL** even if faster.
- Indexed adapter changes any real `read_range` byte: **FAIL**; retain original.
- Low or noisy full-product effect: baseline wins; retire as immediate optimization priority, preserve O194 structural fact.
- Giant file would exhaust resource/time budget: stop safely, preserve partial evidence, no false conformance.

## Ownership and boundaries

O193 PR #521 alone owns ZIP64 streaming implementation. O194 issue #522 owns the diagnostic hypothesis. This branch adds only a new *scientific script, workflow and record* stacked on exact O193 HEAD; do not write O193 Reader/Builder or Discovery STATE, touch neighboring ZIP publication fixes, alter release/format policy, or claim v0.31 promotion. The immutable comparator is O193 Reader method `read_range` on its original exact source; indexed adapter is invoked only by instance-local monkeypatch during its own A/B runs. CI is an asynchronously persistent instrument, not an agent.

Evidence rung: authentic product A/B **only if** actual 4 GiB Builder archive, real installed Reader, full ZIP64 export, and independent stream decode all complete. Otherwise evidence remains partial lower-rung infrastructure/host control.

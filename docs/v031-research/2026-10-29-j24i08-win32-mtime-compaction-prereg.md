# J24I08 — Source-exact Win32 mtime owner composition for private compaction (preregistration)

Date: 2026-10-29 UTC. Status: **PREDICTION; NO PRODUCT RESULT YET**. Base J24I07 HEAD `94acd76dafc7463cc98b3a566041a7334ea966e9`, scientific owner #724 stacked on compaction implementation #723 (`52d51b9446dc8876319f7bd1e6ca2b7f54681de8`). All original J24I07 tests and frozen release criteria retained.

## Exact observed problem
Installed exact-source [three-host run 40808497646](https://github.com/FCMO-AI/.CMPCT/actions/runs/40808497646): Ubuntu 4/4 PASS, macOS 4/4 PASS, Windows 2022 fails before completing first plain case at Reader `extractall(metadata=True)` `os.utime(... follow_symlinks=False)` with `NotImplementedError` (job 123233008451, artifact 12869321519). This is a **product portability veto**, not symlink privilege or benchmark noise.

## Distinct architecture and scientific prediction
Existing independently owned source #504/O167 has Win32 handle-bound non-follow regular/directory timestamp restoration, helper Git blob `70308f454c74fad7b247db6ee36aa8cc7d38c99c`. #513/O180 found a separate failure on symlink mtime and #629/J24H05 composes both. Reuse these source-owned solutions by exact helper **copy** and narrow transplant of its static `_restore_regular_mtime` method into the inherited Reader, replace only the two regular/directory no-follow mtime call sites, and catch `NotImplementedError` (without pathname-following fallback) at symlink timestamp only. No second Win32 native helper is invented.

Prediction: the unchanged J24I07 installed-archive corpus and test, run on all three hosts with this composition, gives exact 4/4 per-host semantics, source and sentinel preservation, hardlink relationship, failed-source destination rollback, public restricted symlink extraction negative. Windows file and directory physical mtimes receive non-follow handle behavior. Method source must match its exact donor and old read/codec behavior unchanged.

## Stronger controls / alternatives
1. Disable metadata in `compact_archive`: makes Windows green by discarding a hard correctness contract; reject.
2. Catch `NotImplementedError` everywhere: restores availability but silently loses real physical file/dir mtime (historic O102); reject.
3. Fork Win32 ctypes implementation: redundant and under-tested versus donor #504; reject.
4. Source-exact narrow donor composition (selected) with unchanged original three-host court, and source/receiver blob checks; any new defect falsifies the composition.
5. Inert typed representation transfer (no scratch filesystem): potentially stronger for concurrency but larger design and unrelated to the already isolated no-follow failure.

## Kill and preservation
Reject on any Windows/Ubuntu/macOS regression in J24I07, any changed output file SHA vs same-host source logical semantics, unsafe public extraction, altered outside sentinel, changed hardlink relationship, or loss of donor reparse refusal. On Windows symlink mtime itself is an optional best effort, not proof of physical symlink timestamp preservation. Do not merge or release: ancestor TOCTOU, crash durability, full official performance, ACL/xattr portability, large tree CPU/RSS/temp I/O and the four inherited historic release assertion failures remain.

## Experimental evidence ladder
Preregister this prediction before product edit. Preserve donor helper *byte-for-byte* and check Git blob. Retain inherited J24I07 test and launch a dedicated exact-head three-host installed Python 3.11 court, source checked against recipient and donor blobs. Save physical input/output and explicit failing receipts, no silent host skips. Local source inspection is not product evidence; isolated successful court is not release evidence. Never edit `docs/discovery/STATE.json` (#574 owner), donor PR #504/#629, main, format, frozen benchmarks, release policy or validators.
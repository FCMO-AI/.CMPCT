# J24I43 — prospective native direct WAV/FLAC streaming integration

**2026-10-29 UTC — preregistration before product source modification.** Research integration only; **DRAFT**, not a merge, release, version, wire, ABI or benchmark promotion. Base PR #784 exact `0faa25827e7393f927252876d40e9f6cb53e5a24`, contains existing #765 fused CRC. Product ownership: same Phased3 native integrity lane #765; #784 is the immutable in-archive streaming oracle. Do not rewrite inherited experiments, tests, performance thresholds or release evaluators.

## Baseline and mechanism
J24I38 physically demonstrated five complete codec-2 reconstructions on a genuine Builder WAV of 32 MiB+44 B: ~5x rchar and ~4.3x wall vs one-shot control, whose peak RSS increased ~24 MiB. J24I42 demonstrates bounded FLAC reconstruction directly inside the original archive with identical logical SHA/CRC and much less physical read/memory but is **not** product-equivalent. In current `native/cmpct-core/src/vzip_dispatch.rs`, `Archive::verify_complete()` invokes `read_range()` in 8 MiB chunks, and each direct-WAV range triggers full `decode_wav_flac_blob()` into Vec. Existing direct-CMA4 CRC and SHA-256 checks must remain.

**Primary question:** Can the production `Archive::verify_complete()` use *the same already-open File behind its Mutex*, a `Take` reader limited to the authenticated codec-2 physical csize, a bounded PCM staging buffer, and one streaming SHA-256/CRC32 pass to verify direct WAV without caching full compressed/WAV content or rebuilding each verification chunk, while leaving ordinary `read_range()` intact?

**Prediction:** The unchanged authentic J24I38 Builder WAV files of 8 and 32 MiB both still return verified count=1; targeted CRC-only header corruption is rejected as BlobHeader; damaged FLAC magic/truncated physical stream is rejected; all computed exact logical bytes/hashes and inherited direct-codec vectors remain unchanged. The source file must not be reopened by path. In process-local Linux trials, native verify should eliminate repeated FLAC decode, with rchar closer to the bounded J24I42 oracle and RSS below the old full-materialization verifier on 32 MiB, but this quantitative gain is **unmeasured until actual hosted execution**.

## Strong simpler controls and alternatives
Keep existing native code (correct but 5x repeated decode); cache complete WAV (measured high memory); add a second full verification traversal (more CPU/I/O); replace generic range APIs (changes broader semantics); integrate narrow direct-codec 2 fast path while preserving other codecs and range paths (chosen). Existing J24I42 research oracle is a *weaker* alternative semantics reference, not a performance-controlled product substitute.

## Kill / narrow
Reject or narrow candidate if authenticated original fails, any original byte/hash differs, CRC-only/FLAC-frame corruption is accepted, direct/non-WAV regressions, source-borrowing violated, unbounded allocation, semantic weakening, failed source identity, or unexplainable CPU/RSS/time regression. A green specialized GitHub Actions workflow is **not** full native/C ABI/extraction/ZIP/recovery, multi-host, nor frozen release evidence. Historical negative results remain immutable.

## Verification ladder
1. Exact source review + small compile/test, confirm call graph changes only direct-WAV *complete verify*.
2. Use actual Builder WAV fixtures and independently audited physical layouts inherited from #784; test original, crc-only and hostile encoded mutation, with baseline native code retained for same-input A/B at separate sources.
3. Audit processed sample counts, stable hashes and resource memory/cpu/rchar; compare released/native control and new product source in *separate exact binaries* with immutable inherited snippets.
4. Test three-platform native core and installed wrappers, then full product release/parity gates before any promotion.

**Ownership/concurrency:** this branch claims the direct codec-2 `verify_complete` fast path and streaming digest primitive only. No other active PR currently claims this narrow product mutation; #765 owns and is the parent integrity seam. The independent #784 research code remains unchanged. If another owner advances the same code in parallel, reconcile source and preserve one rightful owner before shared writes. `docs/discovery/STATE.json` remains a stale cache and is not a lock.

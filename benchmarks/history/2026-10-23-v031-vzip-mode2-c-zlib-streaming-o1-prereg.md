# O1 — streaming native C zlib provider for exact VZIP Mode 2 (preregistered 2026-10-23)

## Authority and distinct lane
Stacked from PR #278 exact `4a6755c407329467dd872416aae898757dcc0a69`, shipping v0.30.0/r24, development base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Prior PR #278 O0 directly **falsified** Rust flate2/rust_backend byte equivalence: 26/28 differences versus CPython zlib, even when decompression succeeded. No canonical Builder/Reader/native dispatch/format/benchmark mutations are permitted here. This is an independent provider **replication/change-of-frame**, not a retry of miniz_oxide.

## Primary falsifiable question (frozen before code and outcome)
If a detached native C process calls linked system zlib `deflateInit2(level, Z_DEFLATED, -15, 8, Z_DEFAULT_STRATEGY)` and only issues `Z_NO_FLUSH` while consuming stdin incrementally and `Z_FINISH` at EOF, does it emit **identical raw-Deflate bytes** to Python's zlib `compressobj(level, DEFLATED, -15)` on (a) the independently frozen 75-byte level-6 VZIP archive member and (b) seven fixed 0/1/6/9 workload families? Is identity retained at different bounded input chunk sizes, or does streaming segmentation itself change exact bytes?

**Prediction:** same *runtime libz provider/version/configuration* should reproduce Python zlib byte-for-byte on the frozen anchor and most, possibly all, 7×4×3 = 84 cross-boundary pairs; there may be segmentation counterexamples. Any first byte difference is a decision-changing negative for that provider/chunk regime and must remain recorded. Same-libz success is *not* cross-version parity or independent algorithm conformance.

## Alternatives and strongest control
1. Existing rust_backend/miniz_oxide O0: 26/28 nonidentical, retained negative.
2. Retained exact Deflate Mode 1: always exact by storing original stream; carries extra payload but is stronger no-regeneration control.
3. Embedding native libz dynamically: potential provider parity on one host but dependency/ABI/version/OS changes may break it.
4. Pinning exact zlib binary or vendored implementation: heavier product/portability burden, out of scope.
5. Keep native mode 2 typed Unsupported: safe incumbent.

## Experiment and accounting
- Reuse PR #278's frozen independent 861-byte r24 archive SHA `febef1d1f1157066204c468d74e81e14c6f79d1490ab2e76e024beed3ce3fb81`, fixed 75-byte content SHA `708bee4f14697a0938db8dffa4b2f2783db2b662bd279ea584e717daf70cb1fc`, and seven deterministic O0 families; levels (0,1,6,9).
- Compile an independent minimal bounded-buffer native C zlib probe with the host C compiler. Read stdin at fixed chunk settings (1, 4096, 65536) and write Deflate stream incrementally, no full-input materialization in the C process. Python harness materializes source for oracle only, logs hashes and exact bytes of golden anchor.
- Test 84 byte comparisons, repeated native emission, `zlib.decompress(...,-15)` agreement and independent source hash. Record runtime zlib version from Python and native `zlibVersion()`, OS/compiler, source Git hashes, process time and maximum RSS when measurable. This is micro/process evidence, never product performance.
- Reject result if archive/source fingerprint changes, native emission is nondeterministic, either stream fails exact inflate, read/write errors occur, or the native binary silently exceeds its input budget. A run that cannot compile or lacks system libz is infrastructure failure, not provider mismatch.
- Promotion requires more than any positive: verified provider/version pinning across supported platforms, full authentic Reader/nested ZIP/ABI correctness, hostile and historical fixtures, streaming bound and decompression/index/integrity/reader accounting, release/performance gates. No product credit for this O1.

## Expected interpretation
- All-equal: C/libz is a possible bounded-memory native regeneration route **only for these runtime versions/cases**, unlike rust_backend; next prioritize provider reproducibility/portability and integration economics rather than new bitstream heuristics.
- Some-different: preserve coordinates; revisit input stream segmentation/flush behavior before attributing failure solely to provider.
- Golden-different: immediate fail for this native recipe/provider with frozen r24.

## Concurrency and release
Unique files and independent branch; PR #278 retains ownership of its O0 vector, Rust experiment and existing workflow. No `docs/discovery/STATE.json` mutation; it is a staleable index with an independent owner. No changes to frozen O0 results. No merge/release/format change.

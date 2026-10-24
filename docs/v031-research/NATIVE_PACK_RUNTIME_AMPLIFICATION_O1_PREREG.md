# v0.31 native S_PACK amplification — prospective O1 product profiling

Date: 2026-10-24. **Status: preregistered / NO RESULT.**
Base: PR #307 `256a263748b9f65b4bc00dd572799e4f00ae06e7`; canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
Owner: independent **read-only native runtime profiling** for Issue #315, not a cache/Reader implementation; PR #307/#314 own fixed-byte conformance. No changes to Rust, Reader, Builder, format, release gate or frozen conformance vectors.

## Primary question and prediction

Does authentic released-build Rust `cmpct_entry_read_range`, on a single open r24 archive with >=128 tiny files sharing one >=100-KiB physical S_PACK, pay an N-fold complete Zstd physical-blob decode/strong-hash cost for N=1/16/128/256 small reads? Prediction: large N increases wall time approximately proportional to N for the Zstd pack; physical RAW sharing is a no-decode control. A scoped one-decode-and-SHA oracle should establish substantial headroom for a *hypothetical* immutable verified-owner lifetime but earns **zero** correctness/product/cache credit.

## Cheaper controls and alternatives

Source inspection already implies N×physical-decoded-byte work, but doesn't measure real C ABI, Python call overhead, kernel caching or Rust allocations. The prior Issue #315 local system-libzstd ctypes O0 is not authentic CMPCT product. A full cache implementation is premature and risks stale-source acceptance. The smallest deciding rung is paired read-only profiling on one runner. Use Builder on deterministic generated text-like 768-byte members, choose only genuine S_PACK owners, require >=128 members in one physical blob, Zstd (codec 1) and RAW (codec 0) distinct corpus regimes; refuse to claim a result if admission differs. Verify all requested byte ranges independently. Source, physical pack, archive bytes, Python package, Rust library, entry order, CPU and exact run are recorded.

## Method and decision

N={1,16,128,256}; 7 ABBA blocks per N on same process/open native Reader; alternate native Rust C ABI A and one-off scoped decoded-buffer B, all logical bytes verified against independent file bytes. B reads/checks/decompresses one physical pack per batch, then slices N independent members. Include first-touch warmup, baseline empty Python loop/ctypes overhead diagnosis, full archive/pack SHA, file count, codec, logical work, physical compressed read byte accounting, estimated retained decoded bytes and repeated raw wall arrays. Track wall and process CPU, Linux peak RSS snapshot; do not present B as an implementation-equivalent product comparison: it deliberately assumes a strong scoped snapshot ownership model and has not proved mutation/same-reader consistency.

**Kill/narrow:** if actual C ABI repeated pack decode is not material compared with baseline overhead, or no generic pack admission exists, retire/narrow cache urgency. If B is significantly better only by skipping per-read source authentication, it establishes a *conditional* upper bound, not a product win. Held-out perturbation: structurally random high-entropy same-size text files to test RAW direct sharing. No threshold changes or replacement of source fixtures.

## Security / economics

A long-lived cache may return stale bytes after external in-place file changes, even when current native reader would reject tampering via SHA on every read. Cache materialization costs >= decoded PACK bytes each live scope, plus synchronization, eviction/invalidation, source identity and portability. This O1 does not solve those gates; its output must explicitly price them. No writes to project shared discovery STATE unless decision-changing truth emerges and concurrency is reconciled. CI success without substantive run/artifact cannot earn evidence. Preserve negative results unchanged.

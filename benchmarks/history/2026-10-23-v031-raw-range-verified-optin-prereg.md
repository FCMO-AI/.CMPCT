# v0.31 — bounded opt-in verified RAW range (preregistration)

**Status:** prospective test protocol, NOT a product or release result. **Source:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`; revision-24 stable. PR #263 is the separate original negative scientist; do not rewrite or replace it.

## Baseline and question

The published r24 Reader optimizes `S_BLOB/CODEC_RAW` `read_range()` to mmap-slice only requested bytes; it does not CRC- or SHA-check the full physical blob. Research PR #263 independently reproduced the 18/18 falsifier and recorded O(N) checksum economics. `docs/HARDENING.md` explicitly says partial RAW ranges are range-local and do not promise whole-member authentication. **Question:** can an *explicitly named*, bounded-cost, SHA-256 + CRC-verified partial RAW endpoint be added WITHOUT weakening the fast existing endpoint, changing r24 grammar, allocating a complete RAW payload, or suggesting cryptographic origin authentication?

## Mechanism / prediction / controls

Add `CMPCT.read_raw_range_verified(name,start,length,*,max_scan_bytes=64*1024*1024)` for direct `S_BLOB/CODEC_RAW` members (and aliases to such members). Reuse validated mmap RAW frame bounds; compute CRC32 and SHA-256 across the **entire** physical RAW content against the committed record; copy out only the requested range after those checks. Charge O(whole-blob) wall/CPU/memory traffic and O(requested-range) new bytes, bounded by max_scan_bytes. A failed budget must fail *before* scanning; unsupported storage must explicitly refuse rather than silently fall back to unbounded `read()`. Do not cache 'verified' status across requests (a mapped file can change after one scan). Plain `read_range()` remains untouched, retaining range-local behavior and its existing contract.

**Positive:** fixed synthetic opaque RAW data with first/middle/end ranges, exact selected bytes, valid zero-length range and a hardlink-alias control when available. **Negative:** one-byte payload corruption with stale CRC; corruption with CRC repaired but original SHA retained; CRC header corruption alone; SHA field corruption alone; out-of-range and over-budget requests; compressed/PACK/sparse unsupported storage; no output on verification failure. Independently compare actual bytes to original source and checksum oracles. If any corrupted input succeeds, pristine data fails, normal `read_range()` changes, or the method scans over budget, the candidate fails. Verify no format/source identity change outside the chosen Reader, tests and evidence.

## Stronger simpler control and alternative explanations

`CMPCT.verify()` already offers explicit full-file SHA checking. `CMPCT.read(name)[start:end]` is simpler and verifies CRC for a direct blob, but currently does **not** enforce SHA in the direct-S_BLOB branch and materializes the whole logical payload. `verify()+read_range()` checks SHA but may decode/materialize all entries, export work and run TOCTOU after scan; new method reduces allocation for one RAW member but not SHA scan cost. No expectation of a speed win over fast `read_range()`. Without new authenticated range-proof format, O(whole-file) work is inescapable for current flat SHA if claiming whole-member digest verification. Revisions and native ABI remain unchanged.

## Evidence ladder / nonclaims

1. Exact-source code inspection and scientific #263 falsifier establish the baseline.
2. Focused independent pytest with authentic Builder+Reader, counterexamples and budget oracles.
3. Exact-head hosted GitHub tests and installed-package run, plus a small repeated same-host CPU/RSS microcourt contrasting existing fast range / SHA-verified option / `verify()`; all raw measurements retained. This is research/product candidate evidence, NOT a release parity gate.
4. General tests/native/fuzz/performance/portability/integrity gates remain mandatory before any merge/release; if inherited four-red CI occurs, use source-pinned PR #259 control and #266 prospective identity instead of weakening it.

## Concurrency / scope

Distinct lane from #263's scientific original-negative, #255/#270 sparse Reader, #258 PACK SHA, #271 public proof/i18n and #273 sparse performance attribution. No overlapping ongoing RAW-range implementation was found at preregistration. A future integration must reconcile their Reader blobs; do not force-update shared branches. Do not edit `docs/discovery/STATE.json` unless primary scientific decision truth changes.

**Promotion floor:** no claim of MAC/signature/origin authentication, no promise of concurrent mutable-input snapshot isolation, no performance advantage over zero-copy range, no unbounded implicit hashing, no relocation of existing fixed controls.

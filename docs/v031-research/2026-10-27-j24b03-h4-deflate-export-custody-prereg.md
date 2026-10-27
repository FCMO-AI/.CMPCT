# J24B03-H4 — fast Deflate-to-ZIP export must honor physical BHDR custody

Date: 2026-10-27 UTC. **PROSPECTIVE**, source-locked extension of PR #609. This record precedes H4 test/instrument/product edits. Previous J24B03, H, H2, H3, P, M and M2 predictions and negative/positive results remain immutable.

## Actual source / observed static route

Canonical release: v0.30.0, r24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. The current H3-guarded source owner is PR #609 exact `068f24af02ef422d9c71e7cfd81ed4e81b032fa6`, Reader blob `0aa5ef60e8dacde07226062b476bc819698807ef`.

`CMPCT.export_zip` invokes `_direct_deflate_stream` for a directly stored Deflate regular file/symlink. Source inspection finds that this specialized zero-recompression path unpacks the physical BHDR but does not check magic, codec, flags, reserved, index geometry or range bounds; the ordinary `_blob` guard added by H3 is bypassed. Strict `preflight_archive` rejects physical unsupported flags/reserved; `read`/ `verify` already reject these bits after H3. This is a **source hypothesis**, not yet a measured product result.

## One bounded falsifiable question

On **the same independently constructed revision-24 signed-index files**, does H3-guarded `export_zip` accept a Deflate BHDR with only `flags` or `reserved` changed even as preflight/read/verify reject it? Can a constant-time physical-header/index/owner guard in the existing fast Deflate stream path reject these malformed files without changing the valid exact compressed streams, ZIP output bytes, format, or performance architecture?

## Predictions, controls and decisive falsifiers

- Builder-independent `wire(kind,CODEC_DEFLATE,128)` produces two positives (`K_FILE`, `K_SYMLINK`), authenticated index, exact PAYLOAD, correct ZIP Deflate stream. Old H3 and new candidate MUST export a ZIP whose sole member decompresses byte-for-byte to PAYLOAD and whose complete output ZIP bytes are equal across arms. Confirm direct-copy path was taken and the ZIP's compressed stream bytes equal the original physical Deflate stream. `preflight`, `read` and `verify` must accept.
- Independently mutate only `flags=1/128` or `reserved=1/65535` in the physical header for each kind (8 hostiles total). Index, raw compressed bytes, expected payload CRC/SHA, lengths, and other physical bits remain identical; archive SHA changes. `preflight`, ordinary `read`, and `verify` reject all 8 on the H3 source. Prospective prediction: pre-H4 `export_zip` **accepts all 8**, while corrected candidate **rejects all 8** before emitting a reusable Deflate ZIP entry. Retain baseline differences as observed, not manufactured.
- Include an additional authenticated direct-owner size contradiction (declared logical 136 versus owner 128) for both kinds; predict pre-H4 export ignores row-size mismatch, candidate rejects. This guards another bypass of prior J24B03's direct-owner custody.
- For a strong control, verify the physical BHDR's source-exact Git blob identity, ensure signed index and payload bytes are unchanged by each one-field mutation, use Python's independent `zipfile` to decode valid outputs, and compare ZIP complete digests + stream extraction. An accepted malformed candidate or rejected valid control kills H4 promotion. If pre-H4 already refuses, retire the conjecture rather than altering acceptance criteria.
- Only O(1) physical framing/owner checks may be added; no per-range SHA, recompression, speculative cache or weakening historical benchmarks. Changed valid direct-Deflate output bytes are forbidden. Any measured material cost must be preserved as debt rather than explained away.
- This does **not** claim complete ZIP export atomicity, full physical payload cryptographic authentication under hostile on-disk mutation, recovery, mutable mmap immunity, all nested-archive modes, whole-product release parity, or consistency of unrelated Reader APIs. A rejected corrupt first row may leave an empty output destination; atomic ZIP export is separate product debt.

## Evidence ladder and concurrency

First land this prediction alone. Then a paired H3-source-versus-candidate wire court on Linux with recorded reader blobs and archive/ZIP SHA; optionally replicate macOS/Windows using the same unchanged fixtures if affordable. Independently audit the receipts and run valid export regression/conformance. Preserve source and artifact identity. PR #569 owns composed Reader, #615 owns hardlink graph validation, #574 owns discovery STATE; no edits there. No version, format or release promotion from this focused experiment. The next decision is whether this guard can be composed into the #569 Reader without additional full-index scanning or loss of the low-copy path.

# J24Z01 — prospective bounded Zstd selective decode preregistration

Date: 2026-10-26 UTC. Classification: experimental native-library oracle; no product or release credit.

## Authority / exact parent
Parent O209 PR #548 source HEAD `a197ab205dac723a2171b53135d111c605b9867b`, active O193 Reader owner #521 at `392112ce859db5a7f85be593c82d1cabc1f5131f`. Published product remains v0.30.0/r24. O209 exact-head hosted Actions #40416071564 / original artifact #12695302699 measured an authenticated 64 MiB direct Zstd S_BLOB selective 1 MiB range: 131372 KiB fresh-child VmHWM increment versus 2588 KiB for the independently chunked control; median difference 125.765625 MiB. O209 used identical logical SHA, but physical container bytes differed (7612 vs 77506). This is strong evidence of decode-unit memory ownership, not of a product repair.

## One scientific question
Can an independent, bounded `libzstd ZSTD_decompressStream` implementation decode the **same single physical compressed frame** for a 1 MiB range, streaming the entire frame for CRC32/SHA-256 authentication, at substantially lower fresh-child kernel VmHWM without silently exporting an unacceptable complete-decode CPU/wall cost?

## Mechanism and strongest simpler control
A = unchanged authentic CMPCT Reader `read_range` using `_blob()` to decompress the entire 64 MiB frame into a Python bytes object. B = independent ctypes research-only `libzstd ZSTD_decompressStream`, input from the exact original S_BLOB record, output in <=64 KiB frames, calculating the complete physical blob CRC32/SHA256, validating logical expected size/segment bytes and consuming to frame end. Both arms must use the **same serialized archive bytes and same source**; use exact original SHA values from original O209 producer. Simpler control C = existing 64 x 1 MiB S_CHUNKS from O209, whose 69,894-byte larger physical archive is an explicit cost, not same-container product parity.

## Prospective predictions and kill/narrow
P1: isolated fresh-process median B `VmHWM_increment` at least 32 MiB below same-archive A on 64 MiB one-frame input, >=3 alternating independent-process trials, excluding fixture generation and Python import from timed library calls. P2: B reconstructed selected 1 MiB bytes exactly; streamed size, physical CRC32 and physical SHA256 match authenticated blob header and full file SHA256 of the original source. P3: B does not consume >64 KiB per library output buffer and stores <=1 MiB selected bytes; report input compressed size and bounded output max, ABI return/error status. P4: median B CPU and wall <=2.0x A for the 64 MiB synthetic source; failure preserves memory result as a conditional science seed with explicit throughput debt, not a product win. Include a different 64 MiB low-compressibility or non-periodic pattern if its production is affordable, disclose source/build cost separately.

Negative/failure controls: flip one compressed source byte, truncate the frame and append trailing bytes; must fail closed or explicitly classify decoder/record invariants not preserved. Different logical output, checksum mismatch, unsupported host ABI, infinite/stalled decode, absent result-bearing receipt or non-comparable timing invalidates positive claim. A measured memory win with >=2x CPU/wall remains REHABILITATION_DEBT, not product readiness.

## Alternatives / opportunity
- Reuse O209's 64x1MiB partition directly: memory bounded but archive grew 69,894 B, unacceptable deterministic size debt for promotion.
- Change Builder chunk admission: higher architecture surface and a different stored representation, conflicts with decoder-owner conclusions.
- C++/Rust native Reader implementation: larger integration and platform burden; tiny streaming oracle can kill or justify it sooner.
- Repeated one-shot library decode with temporary file: exports full decoded I/O, weaker product economics.
- Selected research route: C-ABI streaming, correctness/CRC/SHA fully charged, Linux kernel peak measured before any production Reader edit.

## Scope / governance
Research-only file and independent CI workflow on a branch stacked on O209; no modifications to Reader, Builder, benchmark, comparator, native crate, format, release policy, frozen vectors or Discovery state. Do not change O209 original fixtures or published receipts. No claim of safe general Zstd dictionaries/WAVFLAC/virtual ZIP or full ZIP64 export until separately measured. The weakest relevant inherited fact (O209) controls what is already known; this asks the distinct counter-mechanism question.

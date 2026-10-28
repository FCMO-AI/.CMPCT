# J24G25 — Deflate read/export compatibility court (prospective)

Date: 2026-10-28 UTC
Status: **PREREGISTERED — NO MEASUREMENTS AT FREEZE**
Parent authority: published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / revision 24.
Exact candidate source: PR #284 `2e493d2d941f9c144c0c5050b41c88dc7c6e57dd`, Reader blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`.
Independent alternate candidate: PR #707 `5f66db11dfef60b9d0162e8e04596b142db2570d`.
Scope: **research-only acceptance-parity test**, no mutation to either candidate Reader, ZIP64, frozen experiments, benchmarks, release policy, or common state. This experiment is explicitly distinct from #284's physical-corruption repair, #492's output-atomicity repair and #707's existing candidate.

## Question and controls

Does the existing #284 verified-Deflate export reject an otherwise valid r24 direct-S_BLOB/Deflate member carrying trailing bytes after an otherwise complete RFC 1951 stream, even when the *same installed candidate Reader's* `read()` and `verify()` accept that member? If yes, its `trailing` negative-test classification is stricter than inherited product acceptance and the implementation is **not** a transparent integrity repair.

Strong simple control: a real signed-index r24 file, exact same physical bytes in one process, with plain valid raw-Deflate member (no trailing bytes). We will build a second r24 archive differing only by a consistently reencoded physical stream and index/record/footer geometry, retaining exact original decompressed payload/CRC32/SHA256; control `read` and `verify` must succeed on both or the experiment is invalid.

A separately rooted stdlib `zlib.decompress(...,-15)` check and `zipfile.ZipFile.read` challenge source/extract semantics. Compare `CMPCT.read`, `CMPCT.verify`, candidate `CMPCT.export_zip`, physical original Deflate bytes and output destination preservation. Run on installed exact-head source across Ubuntu/macOS/Windows; source and receipts pinned by SHA, not a synthetic PR merge.

## Prospective prediction and disproof

P1: ordinary bytes: Reader read/verify/export succeed and ZIP decoded bytes equal source.
P2: same raw payload + trailing `b'\\x00\\x01'` inside the committed physical Deflate blob: `read` and `verify` still succeed; candidate #284 `export_zip` rejects with a *trailing bytes* complaint, contradicting exact acceptance parity. The prediction fails if read or verify reject, or candidate exports the exact original member and independent ZIP reader consumes it.
P3: single corrupted physical CRC bit: read/verify/export reject; this preserves the intended #284 safety improvement and must not be weakened to repair P2.
P4: no archive-wide source mutation between operations; compare each operation on identical physical bytes. A failed output must leave an existing destination untouched in the specific #284 prevalidation path. General ZIP publication atomicity is separately owned by #492.

## Alternatives and limits

(1) Strict RFC-1951 framing could be an explicit new product safety policy, but is **not** a transparent repair of the old Reader. It requires deliberate compatibility authority and a targeted release policy, not an implicit test change. (2) Accept trailing data while authenticating the fully consumed logical stream: candidate #707 already explores this; the question is transfer, not duplication or implementation. (3) Recompression sacrifices byte-identical Deflate reuse and could change ZIP semantics. (4) Existing #284 tests already classify trailing as invalid; the untested independent question is whether the same *Reader* accepts those physical bytes before export.

Kill/narrow conditions: if a real r24 archive with valid committed trailing Deflate fails read/verify, retire the hypothesized mismatch; if #284 accepts export, retire it; if mismatch survives, report to #284 and #707 without changing either implementation. No product win, benchmark win or release credit follows a passing research court.

## Evidence and concurrency

Do not touch the source owner #284, ZIP64 #260, archive-output owner #492, or PR #707. This prereg is the first child commit and must predate test/workflow commits. Test artifacts must preserve exact source SHA, Reader blob, original archive bytes and per-case read/verify/export/ZIP-consumer results, including negative branches and failed tests. If CI cannot run, record unmeasured status rather than claiming a result. The Discovery Engine state remains under a separate owner; link to this evidence only when a decision changes.

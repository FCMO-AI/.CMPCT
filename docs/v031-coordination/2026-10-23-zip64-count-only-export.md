# v0.31 ZIP compatibility: count-only ZIP64 evidence (2026-10-23)

Status: DRAFT PRODUCT REPAIR in PR #260. Released r24 and v0.30.0 unchanged.

## Baseline and decisive falsifier

The original Reader Git blob e716233403dabd0966863c45635e18fa5ac6afb8
writes an entire 65,536-entry ZIP, then raises OverflowError at its ZIP32
central-directory count test. The leftover ~6.4 MiB file fails Python
zipfile.ZipFile with BadZipFile. This occurs on a structurally valid, dual-index,
commit-footer r24 archive containing 65,536 empty directories; the native
CMPCT Reader opens and verifies it before export.

Small-count source-identical ZIP controls:
- 65,534: SHA256 31665c00aa3579f8d60f7d9a2824c3b1080c75a32d45edf51514527ec4b8eb4d
- 65,535: SHA256 a9e67a0bceb2297980f77215c61a69178b450920531ba9b148e9bf9879aefc2b36

The proposed native ZIP64 count-only footer emits 56-byte ZIP64 EOCD,
20-byte ZIP64 locator, then the 22-byte sentinel classic EOCD. No local
entry, shared payload, compression method, CRC or central member changes.
The resulting 65,536 and 70,000 entry ZIPs both round-trip through Python
zipfile, and an independently implemented Info-ZIP unzip -t accepts the
65,536-entry output. A 65,537-member sample additionally preserves the
literal raw Deflate stream from an authenticated physical r24 blob.

## Negative and alternative

An earlier safe alternative routed all large counts to stdlib ZipFile. It
restored reconstruction but locally took approximately 0.70-0.75 s rather
than approximately 0.19-0.25 s from the zero-recompression count-only writer.
These are single-run diagnostics, not release timing claims.

Native ZIP64 for cumulative offsets / >4GiB individual members is not
implemented. A conservative pre-output bound accounts for names, ZIP
headers, raw sizes and exact retained Deflate stream sizes; when the bound
exceeds 32-bit offsets, the existing stdlib ZIP64 fallback is used. A
4GiB metadata bound was falsified/verified without allocating 4GiB, but
full large-file product behavior and peak RSS are UNMEASURED. The
fallback's potential whole-member materialization remains technical debt.

## Tests, promotion boundary and continuity

Six complete local targeted pytest cases PASS (count transitions, Deflate
identity and offset bounds). Standard Python zipfile and Info-ZIP are
independent ZIP-format oracles. The targeted GitHub Actions workflow on
PR #260 provides hosted exact-head source custody; see its actual logs
and final result, not this note, for promotion decisions. Full CMPCT
tests, native parity, portability and release performance gates retain
authority. Historical fingerprint reds under Issue #246 are not waived.

The test boundaries 65,534 / 65,535 / 65,536 / 70,000 are deliberately
fixed. Next stage: review PR #260 exact-head hosted proof and reconcile
with Reader and ZIP portability owners. No format change, merge or release.

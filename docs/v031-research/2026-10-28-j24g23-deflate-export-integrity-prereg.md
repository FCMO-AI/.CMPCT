# J24G23 preregistration — exported ZIP integrity from authenticated Deflate storage

Date: 2026-10-28 UTC
Status: PREREGISTERED BEFORE RESULT-BEARING EXPERIMENT
Repo: FCMO-AI/.CMPCT
Frozen source: published main `80c358f8824ec1b20d349c92ed94c898090969b0`
Branch: `agent/phased2-v031-j24g23-deflate-export-integrity-20261028`

## Question and distinct ownership

Does the released `CMPCT.export_zip` direct-Deflate fast endpoint preserve the released Reader's physical-integrity rejection policy on a broken **physical Deflate record**, or can the endpoint emit a ZIP archive with invalid bytes while `CMPCT.read` and `CMPCT.verify` reject the exact same source?

This is a different output surface from J24G22/J24G22b's CLI `cat`/stdout study and does not modify its implementation or evidence. No known current open PR specifically owns direct-Deflate ZIP-export physical-authentication parity. Re-check before shared writes.

## Baseline source and mechanism

`src/cmpct/reader.py` `_direct_deflate_stream` returns mmap-backed compressed bytes and header CRC/size without invoking `_blob`. `export_zip` copies those header fields and compressed bytes into ZIP records. By contrast `_blob` decompresses and checks actual uncompressed length and CRC32, and `verify` further checks file SHA-256.

The plausible failure is not ZIP container formatting; it is **transferring unverified archive-controlled compressed data/CRC into a second independently consumable archive format**. Strong alternative explanation: the authenticated revision-24 index and footer might implicitly guarantee physical Deflate bytes, or `export_zip` might reconstruct the same blob indirectly through another remaining member before emission.

## Preregistered source-exact controls

1. Build a real r24 CMPCT using the published Builder from a physical regular file containing deterministic ordinary data and a nested ZIP entry carrying the same bytes. Confirm it genuinely chooses `CODEC_DEFLATE` physical storage; if it does not, report this and stop instead of silently handwiring an unrelated compressed blob.
2. Remove the nested ZIP logical member through the public transaction Writer to leave the Deflate-backed regular member without a second output dependency. Reopen and verify baseline `read`, `verify`, `export_zip`, and independent stdlib ZIP read/test.
3. Copy the physical r24 bytes and corrupt only the CRC32 field in the Deflate physical blob header. Do **not** recompute authenticated index/footer; they were not changed. Prove unchanged all other source bytes, signed index, original Deflate payload and original decoded content.
4. Compare `read`, `verify`, `export_zip`, `zipfile.testzip()`, and ZIP extraction on the same mutated source. Record complete exceptions and output hashes. A separate compressed-payload bit-flip is optional only if its bit location is chosen prospectively.
5. Test an independent strongly rooted witness: compare exported ZIP central/local CRC values to the CRC32 computed from the original decoded bytes, without trusting the Reader's assertion text.
6. Keep historical published Reader source exact. No changes to thresholds, format, corrupt-test files, or benchmark comparator.

### Prediction / kill conditions

P1: A real first-party Builder+Writer path can produce a direct CODEC_DEFLATE regular member that exercises the shortcut. If not, scope narrows to theoretical parser compatibility and no product claim.
P2: On that real path, `read` and `verify` reject a CRC-mutated source while `export_zip` returns normally and writes an invalid ZIP. If `export_zip` rejects, the main hypothesis is falsified.
P3: No corresponding divergence occurs in the unmutated same-input control; all tests must prove this.
P4: Fix candidate (if P2 fires) must preserve successful ZIP raw-stream byte identity for valid archives and provide at least the same physical CRC/length semantics as ordinary `read`. Measure CPU/wall, output size and exact bytes on valid direct-Deflate controls. Full product/release credit requires independent conformance, adversarial/portability, and current release gates.

## Evidence boundary

An initial code inspection is a hypothesis, not a reproduced product defect. A hosted installed-package experiment with physical files and raw receipts can prove only the cases examined. A source-preserving experimental patch and green specialized tests are not release credit. If the fault is confirmed, preserve the failing unpatched court and separately run the candidate on identical inputs.

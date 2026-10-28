# J24G24 preregistration — verified direct-Deflate ZIP stream copying

Date: 2026-10-28 UTC
Status: FROZEN BEFORE CANDIDATE EVIDENCE
Published base: `main@80c358f8824ec1b20d349c92ed94c898090969b0`
Defect reference: J24G23, https://github.com/FCMO-AI/.CMPCT/pull/706, hosted physical court https://github.com/FCMO-AI/.CMPCT/actions/runs/40772032980
Candidate owner: `agent/phased2-v031-j24g24-deflate-export-verified-copy-20261028`

## Source-exact defect

The released direct `S_BLOB/CODEC_DEFLATE` path of `CMPCT.export_zip` copies unverified physical `BHDR` CRC32 and compressed stream into an exported ZIP. First-party Builder/Writer physical r24 CRC-bit corruption makes released `CMPCT.read` and `CMPCT.verify` reject, yet `export_zip` emit ZIP that stdlib readers reject. This is experimentally verified on published main under J24G23, not merely inferred.

## Hypothesis and controls

H1: validating the *same snapshotted raw-Deflate stream* before copying it, using bounded decompressed-output chunks, CRC32, exact decoded size and SHA-256 header content identity, closes CRC and compressed-stream divergence **without changing a byte of valid ZIP output**.
H2: only Deflate fast-stream export pays added verification CPU and bounded (~64KiB) output memory; output byte size remains unchanged for valid inputs. A complete archive-size/cold-open/CPU/RSS outcome still requires measurement.
H3: the original released Reader remains a falsifying historical control; the candidate must reject the same physically mutated archive **before publication of output ZIP**, and on valid source export must be byte-identical to the published Reader.
H4: frame geometry and malformed/truncated compressed payloads are rejected before exported physical bytes escape. No source mutation between snapshot and validation is allowed; snapshot the compressed bytes once and validate exactly those bytes before returning them.

Strongest alternative: a naive `_blob()` call would reuse the existing decoder but risks cached-data versus mmap physical-stream TOCTOU, and could materialize whole uncompressed files. A full-file decoder is a simple stronger control but exports unbounded memory. Recompression is a simpler safe option but would give up exact stream reuse. A bounded decompression verifier has complexity and portable zlib semantic burden; measure it, and retire/narrow if that burden exceeds value or materially rejects previously valid streams.

## Prospective kill conditions

1. Any corrupted physical CRC source accepted by candidate export: FAIL.
2. Any valid first-party control emitted with bytes different from published export: FAIL.
3. Any valid fixed/published Deflate stream rejected or content changed without an explicit justified compatibility decision: FAIL.
4. Unbounded decompressed output materialization or unbounded step loops: FAIL.
5. Any changed format revision, relaxed integrity, weakened evaluator, or misattributed historical source: FAIL.
6. Performance loss that violates same-runner release timing/no-regression law means research seed may remain but cannot merge/release until debt closed.

## Evidence ladder

- Independent local Python raw-Deflate bounded-verifier random controls (5000 streams, malformed/trailing/truncated) are mechanism evidence only, not Reader product proof.
- Exact head installed product test: historical J24G23 fixture generator run separately on the authentic release to generate identical physical valid/damaged images; candidate installed `CMPCT.export_zip` must reject damaged and produce identical valid output, with independent stdlib ZIP check.
- Host workflow on Linux first; then independent Windows/macOS, full source-head CI, performance/range/large-file tests and release parity before promotion.
- Preserve raw observations, original historical negative court, and negatives. No changes to J24G23 frozen prereg or result. No change to Discovery policy or state with separate owner #574.

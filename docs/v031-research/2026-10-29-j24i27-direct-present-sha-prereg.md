# J24I27 — direct-S_BLOB present-row SHA compatibility and strong-verification contract

Date: 2026-10-29 UTC
Status: PROSPECTIVE PREREGISTRATION — frozen before product/source/test implementation.
Classification: v0.31 draft product-candidate / exact revision-24 interoperability; **no release, merge or format bump**.

## Inherited authority / observed baseline
- Published `FCMO-AI/.CMPCT main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, physical revision 24; Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- [J24I24b issue #748](https://github.com/FCMO-AI/.CMPCT/issues/748) and [#747 source-exact hosted run 40848094637](https://github.com/FCMO-AI/.CMPCT/actions/runs/40848094637) establish that a directly stored file may have an already-present index-row SHA(A) and a self-authenticated physical SHA(B), yet the shipped Reader's `verify()` returns success.
- `validation.py` permits `None` and `b''` member row digests. Independent frozen direct-codec vectors at `tests/conformance/v24-direct-codecs.json` actually encode `None`, so making row hashes mandatory is an unacceptable compatibility change.
- No existing open PR has claimed a direct-*present-row* digest fix; #609/#615/#630 own adjacent size/Reader composition, and #747 owns the original falsifier. This candidate owns **only** the strong verifier's previously ignored optional commitment.

## Primary question
Can the **existing strong verification boundary** enforce a 32-byte direct S_BLOB file/symlink row SHA **when present** while retaining physical blob-header SHA authentication and accepting unchanged historical vectors where the row field is absent? Does this require only constant-time extra comparison after the single preexisting `sha(raw)`, rather than an additional payload scan?

## Competing mechanisms / falsification
- Current simple control: compare decoded SHA only against physical blob-header SHA; known to accept contradictory *present* row SHA.
- Candidate: in `CMPCT.verify`, hash decoded bytes once as currently, compare physical-owner SHA as currently, and **also** compare against row[5] for direct S_BLOB when it is an actual 32-byte hash. Do not change `file_sha256()`, `read()`, `read_range()`, `preflight_archive()`, extraction or r24 format.
- Alternative: make `file_sha256` return row SHA. Rejected: it could stop checking the physical header digest. Alternative blanket required row digest rejected by fixed historical vectors.
- **Kill/narrow:** any failure on unchanged fixed RAW/Zstd/Deflate vectors, any valid `None`/`b''` direct member rejected, any missing rejection for an index-rehashed-but-contradictory 32-byte row, or any duplicated payload hashing/physical SHA loss. If parser/index mutation tooling invalidates real archive framing, classify INVALID INSTRUMENT, not success.
- Stronger hostile control: keep the original physical record unchanged, change only the row digest and **resign both unkeyed index digests** using the exact r24 HDR/FTR protocol. Independently confirm physical header record hash unchanged. The resulting archive must still normal-read but **fail strong verify**.

## Prospective evidence
- Exact three independent fixed builder-unrelated direct codec vectors: RAW, Zstd, Deflate; each baseline original, correct present row, incorrect present row, empty row, `None` row. Check `read` and `read_range` unchanged and metadata preflight where supported; only `verify` is strengthened.
- The exported archive bytes of the unchanged three vectors must remain byte-identical to historical frozen bytes. The modified fixtures are derivative scientific probes with explicit provenance, not replacement golden vectors.
- Require local independently parsed index/footer SHA and record CRC/SHA checks, hosted installed-source CI on PR exact HEAD, all existing tests or explicit inherited failures, and no 0.x benchmark/release credit.
- Record measured scope, failed assumptions, missing native parity, performance/portability/publication debt, and immutable source SHA. Strong proof of indexed content is not cryptographic origin authentication.

## Concurrency / BONK
This is different from the bounded source-FD #746, source mutation #747, and staging publication #741/#745; their owners stay untouched. Cheap targeted tests before whole-product benchmark are the highest-value evidence rung. No Discovery STATE write while #574 has a current reconciliation claim. No validator/threshold/frozen vector changes.

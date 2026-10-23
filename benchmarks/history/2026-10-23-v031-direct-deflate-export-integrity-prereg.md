# CMPCT v0.31 — direct Deflate ZIP export integrity, pre-implementation hypothesis

Date: 2026-10-23
Status: PREREGISTERED / NON-NORMATIVE / PRODUCT CANDIDATE
Inherited owner: PR #260 at 333bea363fc4583abd1a1f33b68f20d2e07ba179; independent falsifier PR #280 at 9bd6473c04c7f43c66b59dfd48af82cbb9790dcf.
Scope: fast `CMPCT.export_zip` direct-Deflate blob copying only; no ZIP64/count modification, revision-24 wire change, frozen benchmark modification, or release claim.

## Observation and simplest control

The current direct-Deflate fast path exports the blob's physical RFC-1951 bytes and trusts its stored CRC without decoding. PR #280 independently reproduced two malformed physical-source cases where `CMPCT.read` rejects and `export_zip` accepts a ZIP that independent `zipfile` subsequently rejects. The simplest correctness control is `self.read(rel)`, but that allocates the entire inflated member and undermines large-file bounded memory. The historical fast copier is the throughput floor.

## Primary falsifiable question

Can a bounded-memory streaming raw-Deflate validator reject a corrupted physical blob **before publishing its ZIP**, preserving the untouched source's *exact Deflate stream bytes* and the independent ZipFile round trip, without a format change or a full uncompressed-member allocation?

## Prediction

On the immutable r24 direct-codec fixture, CRC-header and compressed-payload single-byte mutations will make `export_zip` fail before opening an output file. On valid input, output bytes remain identical to inherited PR #260 fast-copy bytes; the ZIP still extracts exactly. Valid shared physical Deflate blobs are validated once per archive export. Integrity checks use true decompressed CRC32, logical SHA-256, logical byte count, and exact Deflate-end framing, with <=64KiB output buffers and bounded compressed slices.

## Cost and kill/narrow gates

Scientific success requires exact-original ZIP bytes, unchanged ZIP64 count behavior, source corruption rejection, cleanup/no pre-existing-output modification, and bounded transient buffers for Deflate validation. It does **not** earn release credit until a same-source/same-semantics end-to-end export CPU/wall/RSS benchmark tests the added decompression/hash cost against inherited fast copy and stdlib reinflate/redeflate; any confirmed slowdown beyond existing promotion envelope remains explicit regression debt. A source whose ZIP contains intentionally concatenated raw Deflate streams must not be silently accepted as one member.

Alternative hypotheses: a malformed payload may be rejected by zlib independently of hashes, and CRC-only checks may detect the test vectors but are weaker against coordinated CRC changes. The SHA check and no-trailing-stream requirement distinguish these. A mere `BHDR` header check without decoding is insufficient.

## Concurrency and evidence custody

This is a **stacked** branch based on PR #260's exact HEAD, with the independent PR #280 source-exact falsifier as the negative control. PR #260 retains its ZIP64 ownership; this branch owns only validated direct-Deflate copy. Do not merge/publish automatically or attribute parent code as a new contribution. Preserve negative performance evidence. Do not modify Discovery STATE; it is a staleable index, not authority.

# v0.31 — Physical RAW selective-read integrity boundary (2026-10-23)

**Status:** independently falsifiable scientific/contract court; no product, security-patch, or release credit.

## Current source identity and ownership
- Canonical source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- `src/cmpct/builder.py` Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Shipped v0.30.0, format revision 24. This court does not reinterpret any released bytes.
- The `S_PACK` **explicit verify** physical-SHA bug is already owned by PR #258, while the new question here is `S_BLOB` / `CODEC_RAW` **selective-range** integrity. They must not be conflated.

## Preregistered question and disproof
Does `CMPCT.read_range()` of a raw direct blob apply the cheap **CRC32** tier of normal `read()`, and the physical-header **SHA-256** tier of explicit `verify()`? The published format says normal reads use CRC32 where applicable, explicit verification is strong SHA-256, but it does **not** explicitly promise strong authentication of arbitrary partial ranges. The court reports an API-contract discrepancy, **not** an already-established security guarantee or vulnerability severity.

A valid complete revision-24 archive is built on deterministic anonymous bytes. For 64 KiB, 512 KiB and 1 MiB RAW members, corrupt the first, middle or last payload byte **without** modifying the authenticated index/footer. Two variants per position: leave the physical CRC32 unchanged; or update only physical CRC32 while retaining the original physical SHA-256. Inspect a one-byte range, full read, explicit verify and structural preflight.

Prospective expected outcomes:
- Under **unrepaired CRC**, `read_range` returns the modified byte; full `read` rejects; explicit `verify` rejects; structural preflight still accepts because it is not a payload-hash check.
- Under **repaired CRC**, `read_range` and CRC-only full `read` return the modified byte, but explicit SHA-256 `verify` rejects.
- Counterexample / disproof: unexpected failure to build an ordinary r24 file; mismatch with original uncorrupted content; incorrect classifications; a current Reader that validates the range; or a SHA/CRC/index/provenance mismatch.
- This court may return a *different* outcome on a future corrected Reader; preserve original results rather than rewriting history to green.

## Mechanism
The current `S_BLOB` RAW branch of `read_range` computes the mmap slice after examining the physical header; it does **not** verify the decoded RAW payload CRC32 or SHA-256. In contrast, `_blob()` checks the payload CRC32 and `verify()` checks a logical digest against the physical header's SHA-256. A field-level structural preflight cannot certify physical payload bytes.

The simple substitute `_blob(idx)[start:end]` would collapse the selective zero-copy path into whole-blob materialization/CRC work. The alternative `binascii.crc32(memoryview(mm)[base:base+size])` avoids allocating a second full payload, but necessarily reads every byte to prove CRC32; it is **not** strong SHA-256 authentication. An authenticated arbitrary subrange without reading the whole blob would require an appropriate independently verifiable representation/proof commitment, which current r24 RAW headers do not provide.

## Evidence rung: local historical-compatible runtime
An independently archived r24 Reader runtime (not byte-identical to canonical `e716...`) produced:
- **18/18** tampered scenarios classified as predicted: 3 sizes × 3 positions × 2 CRC regimes.
- **18/18** structural preflights accepted while 18/18 explicit `verify` operations rejected.
- All pristine `read`, `read_range`, and `verify` controls passed before mutation.
- Descriptive same-process warmed-mmap A/B/B/A medians in ms (direct 1-byte range → full-blob CRC with zero-copy memoryview): **64 KiB 0.00070→0.01573; 512 KiB 0.00115→0.12209; 1 MiB 0.00126→0.24395**. Eleven four-observation ABBA/BAAB repetitions per size; single local machine. These are not product slowdown measurements or an official release gate.
- Raw local JSON SHA-256 `e0447ff4368c44c23e10d2b5a994fb3bf240d20156cecb1bf9942a056b873118`. Local probe source SHA-256 `92321ff5510e03fb3208b652cd05e824e1f927a7d3876dd77368b267815bdb6e`.
- **Hosted exact-source court: PENDING** until the new GitHub Actions run is read. A green research court will mean the discrepancy is **reproduced**, not repaired.

## Alternatives and decision
1. Leave current selective fast path with clearly documented trust assumptions: zero new runtime cost, but consumers cannot infer CRC/SHA validation from a returned range.
2. Authenticate full physical RAW CRC32 once per Reader/blob and cache the result: preserves the raw representation, amortizes scans across seeks, but adds O(raw bytes) first-access cost, tracking complexity, and only CRC32 strength.
3. Provide an explicit strongly-verified range API/mode: honest semantics but whole-blob hashing/reading cost on r24, and potentially a new caller contract.
4. Design independently authenticated units/Merkle proofs in a prospective future representation: allows bounded proportional range authentication but needs format/native/portable proofs and charged index bytes, and must preserve inherited r24 fallback.
5. Always promote `_blob()` in the range path: simpler but likely violates the released fast-range locality/cost goal; reject until complete same-input product evidence justifies it.

**Current decision:** establish the exact-head discrepancy and preserve alternatives; do not silently insert O(whole-blob) work into a performance-critical selective path before defining the expected verification contract and testing the strongest control. A byte difference does not automatically imply a public vulnerability without a promised trust boundary.

## Scope, concurrency and gates
- Isolated research workflow + source only, no Reader or native mutation; no overlap with PR #258's physical `S_PACK` verify implementation or #255's sparse extraction.
- Full product, native ABI, hostile structural parser, release parity, throughput, RSS, streaming, platform and recovery tests **UNEXECUTED** for a repaired candidate.
- CI and performance gates unchanged; version and format unchanged. No compression or release claims.
- Do not update Discovery Engine `STATE.json` for a secondary research probe; its primary Bounded Drift productization question is separate and its cache is already stale relative to hosted evidence.
- All bytes/names generated synthetically; no client, private corpus or personal data.

## Next cheapest decision
Verify exact-head result. If confirmed, test a zero-copy full-RAW CRC once/cache policy on held-out sizes and genuine mixed streams while preserving precise locality/CPU/RSS. If CPU debt is unacceptable or strong range authentication is required, route the problem to a distinct authenticated block/proof representation instead of optimistic full-blob work. Coordinate semantics with the r24 Python/native handler parity owner before a product PR.

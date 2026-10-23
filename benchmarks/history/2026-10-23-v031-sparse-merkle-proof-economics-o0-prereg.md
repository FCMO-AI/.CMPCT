# v0.31 O0 — Sparse logical Merkle proof economics (frozen preregistration)

**Status:** RESEARCH-ONLY; no CMPCT product, r24 index/format or release change.
**Frozen before result-bearing hosted execution:** 2026-10-23, commit created by GitHub file API.
**Source base:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
**Evidence tier:** O0 independent Python model with synthetic gifted exact extent positions. This is explicitly *not* a CMPCT Reader/Builder or a stronger r24 SHA-256 implementation.

## Current product fact and unresolved question

PR #270 performance run 39984731549 measured about +101.6 ms for sparse library extraction; PR #273 instrumented about 92.9 ms spent hashing logical zero holes of a 128MiB sparse source. r24 commits to the conventional flat logical SHA-256. Treat that digest as immutable in r24; no alternate root can replace it.

**Primary O0 scientific question:** Could a *different, explicitly versioned future* commitment to byte-exact logical files use sparse all-zero subtrees and charged leaf digests to make full-file and selected-read integrity work scale with occupied leaves rather than logical holes, while refusing adversarial offsets/length/payload mutations? If the model has no favorable upper bound under fully charged representation bytes, do not implement it in the product.

## Hypothesis / baseline / decisive disproof

- Comparator A: conventional `hashlib.sha256()` streamed over every logical byte, including zeros. It preserves the actual r24 logical digest semantics, and by design its digest **must differ** from the candidate Merkle root.
- Candidate B: 64KiB logical leaf hashes, domain-separated internal hashes, file-size-bound root, reusable all-zero leaf identity, and explicitly charged 48-byte header/root plus 40 bytes for *each* non-hole-occupied leaf (8-byte index + 32-byte SHA). Decoder-visible extent coordinates are gifted by the synthetic source generator, not product evidence. Proof siblings must be computed from the complete charged leaf index and must be validated against the root.
- Predict clustered 128MiB / 4MiB occupied bytes: O0 candidate median wall <= 25% of flat digest, with <= 3KiB charged additional proof/index metadata.
- Predict distributed 1-byte-per-64KiB-leaf 128MiB hostile: savings disappear (candidate median wall >= 80% of flat), and index cost >= 80KiB. Dense 16MiB is a negative/control, not a success claim.
- Predict changing hole locations, payload bytes, logical length or proof siblings while keeping the original root must fail; no false pass is allowed. A root/index forged *together* is outside origin authentication without a separate trusted anchor, just as r24 flat digest is not a MAC.

**Kill/narrow:** missing byte-exact reconstructed leaf checks; uncharged decoder-visible positions/hashes; implausible costs on clustered data; any hostile mutation accepted; inability to recover root from decoder-visible charged index; experimental selection via fixed fixture identity; or product claims without end-to-end Builder/Reader conformance. If dense/fragmented cases lose, restrict applicability by generic sparse-leaf occupancy rather than tuning away negatives.

## Method / costs

Synthetic deterministic anonymous extent families: clustered, boundary-shifted, all-hole, 1-byte broadly scattered, dense, and short partial tail. Exact equal-length logical data for A and B; print repeated alternating wall+CPU raw samples, SHA identities, extent counts, total bytes, touched leaf count, theoretical hashed data+zero bytes, index charge. Use an independent byte-slice oracle to check generated Merkle membership proofs including hostile siblings, content and length. Protect frozen comparator/threshold and avoid media claims.

Measure further before any product attempt: artifact bytes including full index/root/offset encoding, Builder discovery time, Reader integrity performance on materialized sparse extents, extraction I/O/RSS, selective reads, recovery, adversarial ranges, native portability and cross-implementation conformance. Existing r24 flat SHA remains mandatory where its contract requires it.

## Concurrency / ownership

PR #255/#270 own sparse product extraction; PR #273 owns its cost attribution. PR #274 owns optional RAW-range flat-SHA proof. This independent branch owns **only research Merkle accounting**, not any product Reader, Builder, source-selection, current archive format, release or existing state cache.

## Decision rule

Promote only an O0 *research seed* if clustered wins survive index charge and all hostile checks. Explicitly preserve distributed/dense negatives. Never count this as product speed, format, authenticity or release credit. A future versioned-format proposal would require a separate preregistered product court.

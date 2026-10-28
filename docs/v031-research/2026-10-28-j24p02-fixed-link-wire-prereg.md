# J24P02 — Independent revision-24 link-tree wire conformance (preregistration)
Date: 2026-10-28 UTC
Status: FROZEN PREDICTION BEFORE INSTRUMENT OR GOLDEN IMPLEMENTATION

## Authority / baseline / concurrency
Canonical release `FCMO-AI/.CMPCT main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0, revision 24. This is a **research/conformance-only** branch, no product code, format, benchmark or version change. Read repository `AGENTS.md`, `AGENT_HUB.md`, Discovery Engine and the hardening/format/performance/release law before selection. Existing #307/#705 own fixed `S_PACK`, #313 owns typed filesystem digest, #610/#693 own hardlink size contradictions, #262/#621 own forward-hardlink extract ordering, #690/#699/#704 own signed extraction quota / integration. Do not alter or duplicate their implementation.

## Primary scientific question
Can immutable revision-24 **Builder-independent** bytes encode a directory, a real regular owner, a same-inode hardlink alias and a safe relative symlink, with exact `CMPCT.read`, `read_range`, `verify`, strict `preflight_archive` and platform-appropriate extraction? Will the authentic installed Reader accept **both RAW and Zstd physical-record encodings** of the exact same logical tree?

## Baseline, mechanism, control
Published Reader and Builder use seven-field logical rows, direct `S_BLOB` physical ownership and `K_HARDLINK` target paths. A Builder-produced tree can hide common-mode mistakes. The stronger control is fixed, explicitly frozen, separately framed complete files with dual authenticated indexes, 2 physical blobs, distinct link target content, no CMPCT imports during generation, SHA-256 of both the archive and reconstructed content, and an independent wire referee. This is conformance/evidence enablement, **not** compression, speed, security completeness, or a new format.

## Prediction / disproof / limits
- Independently construct two complete r24 archives with exactly 4 rows: `tree` directory; `tree/00-owner.bin` regular; `tree/10-alias.bin` hardlink to owner; `tree/20-link` symlink to safe relative target `00-owner.bin`. Owner sorts before alias to isolate representation from the already-owned forward-hardlink extraction-order problem.
- Physical blob index 0 owns regular content and index 1 owns the relative symlink target. Both RAW and Zstd variants must reconstruct identical logical bytes and file-type relationships.
- Strict preflight must accept the two unmodified archives and reject independently rehashed malformed hardlink missing-target and invalid symlink blob-index variants. Ordinary installed Reader full reads, ranges, `verify` and extraction must match the frozen answer where host supports symlinks/hardlinks; any platform skip must be explicit rather than counted as a pass.
- A counterexample is any decoded byte mismatch, wrong link relation, invalid original fixture, different frozen original SHA, unexpectedly accepted strict hostile, or failure of the independent non-CMPCT index/physical audit. Unexpected release Reader behavior is recorded as a negative; do not rewrite the oracle around it.
- Mutated archives rehash metadata only, not physical blob bytes. Neither unkeyed SHA-256 index digest is a digital signature.
- Raw archived bytes, read/write operations, resource cost and platform provenance must be reported honestly. Any CI workflow must pin exact PR-head SHA and retain artifacts.

## BONK and future value
Alternative A: repeat S_PACK host tests — already answered #705, no.
Alternative B: build another adaptive compression codec — lower prospective correctness value while extraction/Reader debt is active.
Alternative C: builder-only filesystem roundtrip — cheaper but weak common-mode control; #313 already covers a distinct typed digest.
Chosen: cheapest independent fixed-wire frozen identity that closes a documented conformance gap under `docs/HARDENING.md`. If this proves only Reader/Builder agreement, retire; if it provides source-independent truth, preserve it as a portability and native-ABI transfer seed. Do not claim universal cross-OS semantics for symlink creation without actual host tests.

## Ownership and continuity
This branch alone owns `tests/conformance/v24-link-tree.json`, `tests/conformance/generate_v24_link_tree_golden.py`, `tests/test_v031_link_tree_fixed_golden.py`, optional `research/j24p02_link_wire_referee.py`, and its dedicated CI workflow. Keep Discovery state unchanged while #574 owns reconciliation. Results may update this branch's own result note, not historical frozen files or neighbor branches.

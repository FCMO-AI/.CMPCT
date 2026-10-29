# J24I24/J24I24b — hosted observed result and source-level review (2026-10-29 UTC)

**Status:** `SCOPED_SOURCE_MUTATION_FALSIFIER_CONFIRMED; RELEASED_READER_DIRECT_ROW_MISMATCH_CONFIRMED; NO PRODUCT PROMOTION`. Source owner: PR #746 exact `ef83fe091509b07908646cd048278def715200b2`. This branch is **research only**; code in `src/cmpct/**`, published `main` v0.30.0/r24, format, tests and historical gates are not modified.

## Decision chronology (immutable predecessors retained)

1. Prospective J24I24 prediction at `204ba38c3ca582c836903cdfe9e2438ea118fda9` expected Linux shared-mmap ABA could evade first/last full physical SHA and fstat, but assumed the installed Reader would catch index-row hash A versus copied physical SHA B.
2. Initial exact-source installed-host [Actions #40847730388](https://github.com/FCMO-AI/.CMPCT/actions/runs/40847730388), HEAD `95beec19ef29338f4e094c07d7bae8a65920a3a3`: **FAILURE**, 2/3 tests PASS, third failed at the final `Reader.verify` rejection assertion. All preceding ABA bridge conditions had executed; the unexpected Reader acceptance is a genuine negative for the original oracle assumption. Do not retroactively call this tribunal a PASS.
3. Separate J24I24b prereg at `6a6b48b8a8a9c5748fdf3f774bc191c9c10e122b` preceded the new direct-row test and the corrected expected outcome for the original test. It prespecified one Builder-independent static case, no source mutation/relay, with an unmodified authenticated index row SHA(A) and an independently coherent RAW B physical record.
4. Final source-test HEAD `88486d3b49c8a5d258ff52fb233999c3f2fcc3b2`, [Actions #40848094637](https://github.com/FCMO-AI/.CMPCT/actions/runs/40848094637): **SUCCESS 4/4**, Ubuntu 24.04, installed exact source; three basic controls plus independent direct-row mutation. Source-test and donor Git identities recorded in workflow artifact. No product code modification.
5. Engineering Evidence initial failure for missing dossier headings, later for two missing markers; PR body corrected, the unchanged-result code-head [Engineering Evidence #40848431949](https://github.com/FCMO-AI/.CMPCT/actions/runs/40848431949) **SUCCESS**. CI Topology, Version Discipline and R36 Attribution on original source-test HEAD **SUCCESS**. General test suite result must be checked separately and is not asserted green here.

## Raw decisive observations

Stable A source and ordinary direct B replacement both have **1,588 bytes** in independent r24 vectors. Ordinary control source/target physical SHA-256 identical: `9ed76eb08ece08dff6eab2ba9be7e65655010015dc84e0f09b469d5eeeefabcb`. The **permanently modified** source control is rejected before publication.

Hosted ABA case: pre/post source SHA = `9ed76eb08ece08dff6eab2ba9be7e65655010015dc84e0f09b469d5eeeefabcb`; pre/post `fstat` tuple unchanged (`dev,ino,size,mtime_ns,ctime_ns`); output physical SHA = `a19eb91861318f8a7bc0e8c4b4e15a1d8aee9a5a582a9d8926617ba4d9143496`; one B physical record copied with valid SHA-256/CRC32; the source was restored exactly to original A. One controlled injection and one restoration occurred while the source was held open. This falsifies the inference that source FD + fstat + two complete file hashes certifies a point-in-time snapshot against same-permission shared mmap mutation. It does **not** falsify the bounded-memory source-FD streaming oracle under stable-source conditions.

Direct Reader question: original logical indexed row digest `SHA(A)=6ab72eeb9e77b07540897e0c8d6d23ec8eef0f8c3a47e1b3f4e93443d9536bed`. Physical B blob digest `SHA(B)=9b6ce55f379e9771551de6939556a7e6b949814ae27c2f5cfd5dbeb378ce7c2a`. The unchanged primary and duplicate index copies identify row A; independent raw `struct` parser checks B CRC and SHA, and unchanged released Reader `CMPCT.read` returns B and `CMPCT.verify()` returns 1. Released and research-parent Reader share Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. This is independently reproducible without ABA/compaction. Tracked in [issue #748](https://github.com/FCMO-AI/.CMPCT/issues/748).

## Mechanism and important semantics qualification

`Reader._blob` checks CRC32/length, `file_sha256` on direct S_BLOB returns the physical blob-header digest, and `verify()` compares SHA(decoded bytes) with that physical digest rather than row[5] when present. Builder ordinarily records row[5] SHA(raw). **However** revision-24 `validation.py` explicitly allows absent hash in a file row and comments that direct-file hashes are inherited from physical blob headers. Therefore this result proves acceptance of an internally contradictory *present row digest*, but does **not** alone prove that mandatory row-digest binding is a settled format-law requirement for all historical archives. Future product change must make that compatibility decision explicitly.

The parent source-FD relay's whole-file SHA is **not keyed authentication** and physical blob CRC/SHA can be recomputed by an actor with write authority. No remote exploitation, privilege escalation, probability-of-race, or published-main compaction defect is claimed. The published Reader behavior is a narrower static consistency problem, not a cryptographic signature bypass.

## BONK / alternatives and scientific value

Primary science: source FD can reduce physical-memory dependence (#746) while **not** establishing immutable source ownership (#747). The stronger control is a trusted source snapshot or exclusive writer contract; merely polling fstat or replayable SHA before and after is insufficient. Both can export temp bytes, I/O and latency, still unmeasured.

Independent static consistency issue: source/head self-authentication can coexist with contradictory indexed row. The cheapest causal guard to evaluate is checking present 32-byte row SHA against the already decoded real bytes during strong `verify`, while preserving optional row hash semantics. Comparing *two claimed SHA declarations* without hashing data would not provide strong physical integrity.

**Counterfactual discriminator:** the cheap Builder-independent 1,588-byte direct-row A/B mismatch test would have exposed the source of the first Reader-verdict surprise before constructing an ABA scenario. It was prospectively recognizable from the two trust owners in `Reader.file_sha256` and row[5], once that owner map was examined. This is a local experiment-selection lesson; one result does not authorize rewriting `DISCOVERY_ENGINE.md`.

## Pending promotion debt and handoff

- No product change, merge, release or version/format bump. No storage/CPU/RSS advantage claimed from J24I24.
- Other codecs, sparse/pack/CDC, symlinks/hardlinks, native Reader, Windows/macOS, PowerLoss/atomic publish and production compaction cost not tested. Shared mmap hostile case tested on Ubuntu only.
- Issue #748 is the independent source-exact product contract question; #569/#609/#615 own adjacent Reader/geometry integration. Preserve their ownership and explore compatibility before adding checks.
- #746 remains the research streaming owner; #741/#745 own stage FDs and cleanup. [Handoff comment](https://github.com/FCMO-AI/.CMPCT/pull/746#issuecomment-6492802074) is durable.
- This source-test branch holds the raw test and preregistrations. The strongest unclaimed cheap experiment is direct S_BLOB row-optional historic-vector compatibility plus independent preflight/Reader/ABI differential adjudication; do not just repeat same ABA case without new information.

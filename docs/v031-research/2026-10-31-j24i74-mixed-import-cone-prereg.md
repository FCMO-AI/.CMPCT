# J24I74 — mixed signed-journal and sparse-xattr transfer of the import-cone Owned Reader

Date: 2026-10-31 UTC. **Prospective preregistration; commit this contract before any implementation or result.** Research-only, zero product/release/version/format/ABI credit.

## Authority, ownership, and primary question
Released baseline is v0.30.0/r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Scientific parent is J24I73/#878 exact `a6695ba86d6a5b20eaced4eb8b54768f00724c9b`, which ablated the original Owned Reader's research import cone and proved DELETE-only fresh-process economics. #823 owns Owned algorithm semantics; #795/#817 own product signed-journal and hardlink/xattr implementation; #574 owns shared Discovery state. This distinct work owns only a small **held-out mixed-signed-operations interoperability/falsification court** with no product patch and no mutation of those owners.

**Question:** Does the unchanged AST transplanted J24I73 minimal Owned Reader preserve the publicly verified on-disk revision-24 semantics of a real 63-generation **21 RENAME + 21 DELETE + 21 PUT** public Writer archive, including sparse xattrs and tail recovery, across actual hosts? This is a hard generality boundary before any Reader productization. A mere DELETE-only warm-open or import win cannot answer it.

## Baseline / strongest controls
Use the current repository's frozen `j24g73_reader_open.make_archive(..., "mixed", strict_xattrs)`: 128 authentic regular files, 63 public transaction APIs and 118 final members. Compare on the **same physical archive bytes**: published `cmpct.reader.CMPCT`, original `j24g74_owned_decoder_court.OwnedCMPCT`, and a newly generated ephemeral minimal module produced solely by inherited `j24i73_owned_import_cone.generate_minimal_module`, with five source ASTs untouched. The `j24g73` public-vs-factored oracle is an additional stronger inherited semantic control, not a source of asserted credit. On Ubuntu/macOS require genuine filesystem xattr setting and restoration; on Windows record **no physical xattr claim**, but require all 63 authentic mixed operations and logical parity. Never treat an unsupported xattr OS as a metadata PASS.

## Locked prospective hypotheses and kill conditions
- **H1 exact semantics:** On all three OS families, all three Reader classes must agree byte-for-byte on packed index, member names, all 118 raw content SHA-256s, verified count and 63-generation depth; original and minimal routes must be `owned-fresh-decoder`. All three restore identical member bytes and public preflight must agree. One mismatch is a **FAIL** (not a timing win).
- **H2 sparse metadata:** Ubuntu 24.04 and macOS 15 must preserve the exact source-attested sparse xattr mapping and physical extracted xattrs under `require_xattrs=True`. A skipped/unsupported physical xattr is a **host blocker**, not a PASS. Windows is tested with physical xattr requirement disabled and that limitation reported explicitly. No hardlink fidelity is claimed.
- **H3 recovery:** For both a changed terminal digest byte and a truncated terminal footer, all three classes must agree on recovered index bytes and recovered depth; the test must reject an impossible short-format archive for every class. A bad outcome kills the import-cone generality claim; no fallback may silently erase an authenticated 63rd operation.
- **H4 physical / receipt custody:** Each actual archive is retained and hashed before and after all reads. A separately executable referee that does **not import CMPCT** must parse/verify primary r24 index and the 64 original footer payload SHA-256s and ancestry, independently count 21 ren / 21 del / 21 put, check primary uncompressed physical records where supported, reproduce raw timing medians, verify source AST hashes and reject at least five forged receipt or archive alterations. There is no product credit for the independent parser.

## Measurement, precedence, and honest scope
Record complete archive bytes, Builder/public-Writer elapsed wall (separate), six balanced in-process Reader-open wall/CPU observations per variant (descriptive only), 118 complete reads and SHA checks, physical xattr/extraction, preflight and recovery. Existing exact-HEAD tests and CI topology are separate from the scientific court. No prospectively imposed speed-win threshold; **semantic truth dominates time**, and small mixed-N measurements cannot be extrapolated to arbitrary filesystems. No cold-process/installed-wheel/native/large-N/simultaneous-mutation/hostile signed pointer/atomic-snapshot guarantee.

## Alternatives / BONK
- Repeat DELETE-only J24I73: already answered and structurally weaker.
- Rewrite product Reader immediately: overlaps #823/#795 and bypasses hardlink/xattr/recovery gates.
- In-memory oracle without actual physical Writer and extraction: cannot settle r24 xattr ordinal or signed journal semantics.
- Full 15-row product benchmark: expensive and does not directly decide this correctness fork.
- New checkpoint or on-disk format: exports bytes and is unnecessary to test this import-cone hypothesis.
The cheapest decision-changing rung is the authentic mixed Writer physical court on three hosts with a differently rooted footer referee.

## Terminal decision / handoff
A red establishes an exact failing source/OS/metadata/recovery scenario to report to #823/#878 before integration. A green is **only** a scoped hard generality control supporting the next staged product integration gate; it does not justify merge into public Reader or release. The next unclaimed test must address hardlink ownership, arbitrary interleaving, hostile pointer history or native parity without colliding with their current owners. No change to shared `docs/discovery/STATE.json` or its policy.

# O14 — Bounded native hardlink-owner ordinal (prospective preregistration)

Date: 2026-10-24 UTC. Status: PREDICTION FROZEN BEFORE CODE IMPLEMENTATION. Research/product candidate, not release authority.

## Question and source custody
O13/O13b [PR #343](https://github.com/FCMO-AI/.CMPCT/pull/343), hosted run 40086479175, demonstrated two genuine r24 trees with different hardlink ownership but byte-identical published native C transcripts. The authoritative native reader parent is [PR #326](https://github.com/FCMO-AI/.CMPCT/pull/326) exact SHA `43ba79f9b9395af22a0f408de565704c268a4758` (secure duplicate-map + PACK read/owner). This branch changes only native Rust/C ABI plus a separate test court, not Python Reader/Builder/Writer, released r24, or frozen historical judges. PR #342/#348 are separate Python validation owners. Discovery STATE.json is a staleable cache, not a lock.

**Primary hypothesis:** the smallest useful consumer-independent answer is an optional native `cmpct_entry_hardlink_owner(archive, index, out_index)` returning a same-handle terminal regular-file entry index. An index-backed, nonrecursive, bounded graph resolution can reject malformed ownership graphs at archive open in O(files + hardlink edges), without decoding file payloads or allocating hardlink-size output buffers. O13's two formerly indistinguishable real archives must now yield distinct owner ordinals, sufficient to reconstruct POSIX inode equivalence classes after safe destination publication.

## Alternatives / PARETOBONK
- A per-hardlink path-string copy/size-query adds string lifetime/buffer semantics and requires consumers to reparse, normalize and chase graph edges, inviting divergent cycle handling.
- Reconstruct owner by comparing content hashes is scientifically impossible under O13b: alias bytes are unavailable over existing ABI and identical bytes do not imply same inode.
- A general native tree extractor encloses all semantics but is disproportionately large before exposing one missing relationship. It also inherits destination trust, sparse/uid/xattr, recovery and filesystem portability debt.
- A bare target-index query without terminal resolution exports graph CPU-amplification and cycle handling to every client. A bounded owner ordinal is the better product kernel **only if** validation/CPU/memory cost is controlled.
- Strong simpler control: current native C ABI unchanged, plus authentic Python Reader reconstruction; do not claim compression or full extractor speed improvement.

## Frozen pass/fail protocol
1. Build two real Builder r24 files with a.bin and b.bin distinct bytes, same metadata, and z_alias hardlinked to a vs b. Independent Python reader/index confirms each exact link target and content, while native hardlink query returns **different correct entry ordinals**. Old `cmpct_entry_read_range` remains UNSUPPORTED on alias (no covert semantics change); regular bytes unchanged.
2. Test query nonhardlinks, bad index, null output, null archive, zero-valued failure output, and valid alias-to-entry-zero. Query never returns a borrowed pointer; key/ordinal meaningful only within the opened archive handle.
3. Independently mutate and reauthenticate actual r24 index rows (both index copies when needed): missing owner, self-cycle, multi-alias cycle, reference to directory or symbolic entry, unsafe target path, wrong-size target, and valid multi-hop chain. Invalid graphs must reject at native open, valid chain must resolve to terminal regular owner. The mutation generator and oracle must not invoke the native resolver implementation.
4. Held-out adversarial stress: increasing valid hardlink chain lengths versus flat stars with the same file count; no quadratic explosion or recursion/stack overflow; charge parse CPU, archive bytes, peak RSS. A budgeted source-level derivation is lower evidence than hosted measurements.
5. Cargo fmt, clippy, native Rust tests, all inherited native secure-index/PACK controls and exact-head CI. No benchmark promotion based on unit checks or a skipped official release benchmark.

## Kill/narrow conditions
If legitimate r24 Builder files are rejected; if O13b remains native-indistinguishable; if accepting a cycle/dangling owner is possible; if another parser/control variant is simpler with equal safety and lower total cost; if size/CPU/RSS penalties on large ordinary archives are unacceptable; or if native ABI source/header/test diverge, preserve a negative and do not promote. Keep inherited 0-byte size gate, exact filesystem semantics, ABI error/status contracts, and v0.30 release/fingerprint records unchanged.

## Resource/portability and handoff
Input index size stays bounded by native MAX_INDEX_BYTES, MAX_FILES and MAX_PATH_BYTES; graph walk is iterative. The owner ordinal does not itself write/create hardlinks, authenticate mutable physical payloads, or verify release portability. Linux hosted evidence is a partial court only. O11 extractor owner #337 and O13 research owner #343 receive results after a decision; no concurrent source overwrite.

# J24G55 — prospectively registered shared journal replay / preflight parity

Date: 2026-10-29 UTC
Status: PRE-RESULT; draft experiment/candidate only; no promotion.
Parent/owner: #783 at `47ddedbeb844a8d59e9d142910c6705301214ce0`; physical negatives #786/#787 (J24G54a/J24G54b), three-host integrity parent #778. This child must not mutate their branches.
Exact inherited Reader blob: `c82ab200bf849f844587683992f0c702cc39059a`.
Exact inherited validator blob: `10d67553d1c8ff5399dbadc0fcfd5f3c54ea846a`.

## Problem / question / baseline
Two real signed Builder→append_delete revision-24 courts on Ubuntu/macOS falsified validator/Reader parity: J24G54a preflight rejects a valid late-survivor xattr (out-of-range stale ordinal); J24G54b accepts an effective index that assigns the xattr to the wrong *in-range* survivor. Both share a duplicate journal transformation: validation._apply_delta operates on row names without positionally rebinding fsmeta, while Reader._apply_journal_ops preserves original path identity. Inherited Reader verifies and restores correct native xattrs; this is **preflight** debt, not a claimed Reader failure.

## Hypothesis and decision
Extract the currently measured Reader journal identity transformation into one import-cycle-free shared module; route both Reader/Writer and bounded preflight through the *same* function. Preflight retains all prior malformed-operation schema checks, blob caps, max-files budget and footer recovery; new module adds an optional fail-closed per-insertion max-files ceiling without changing the normal Reader path. This should make equivalent index states identical after each committed valid op, remove both physical mismatch modes, and preserve no-xattr, homonymous delete+fresh put, rename, replacement and checkpoint semantics.

## Alternative actions / PARETOBONK
- **Simple clamp/drop stale ordinals** rejected: J24G54b demonstrates an in-range wrong-owner association.
- **Duplicate rekey implementation inside validator** rejected: leaves two authorities prone to semantic drift.
- **Import Reader dynamically into validation** rejected: Reader already imports validation; cyclic dependency and startup overhead are needless.
- **Shared module without reader API changes** selected: move function byte-for-byte except bounded optional file cap; keep a reexport in reader.py and no new wire/format/codec semantics.
- **No product change** safe but leaves independently reproduced incorrect preflight judgments.

## Prospective falsifiers and controls
1. Real Builder archives with genuine native xattrs, appended signed delete; both J24G54 out-of-range/in-range patterns must have structural preflight PASS and effective-index fsmeta equal to Reader; strict native extraction must match source values.
2. No-xattr and early-attribute-only controls remain accepted; corruption/hostile index/footer controls must remain rejecting.
3. Independent same-source in-memory differential with xattrs+owner_overrides under insert/delete/rename/replace, delete+same-name-put, multiop and checkpoint-like replay; source schemas/size limits must not weaken.
4. Malformed operation types, invalid fsmeta ordinals, over-budget file additions and footer-recovery paths must still fail closed or recover to valid older committed version as previously specified.
5. Physical archive bytes and format revision 24 must not change; no Builder encoding, compressor, native ABI or published release mutation.
6. Cross-platform installed source identity and CI; historical #786 negative reproduction intentionally flips its predicate after a fix and must **not** be weakened or rewritten.
7. No release performance credit: micro and observed preflight CPU/RSS/test durations are scoped, broad create/extract/ZIP/Zstd parity remains pending.

## Kill / narrowing and alternative explanation
If the shared helper still yields different effective indices on authentic committed archives, the hypothesis is falsified. If code introduces a valid-archive reject, an unsafe malformed-input accept, resource overrun or recovery regression, integration is blocked. An apparent green from a test comparing only path names without validating xattr byte identity is insufficient. New code is a research candidate, not release authority.

## Concurrency and scientific custody
No concurrency protocol/claims script was found at the parent HEAD. #783 owns the existing xattr-guard validator; #773/#778 own Reader journal fsmeta; #786 owns immutable negative physical evidence. This is a new child branch, never a blind edit to those owners. Do not modify shared Discovery STATE (owned by #574), historical counters, frozen evaluator or preregistration predictions. Outcome must append separately after result-bearing tests.

## Resource / portability / release law
ParserLimits defaults remain; max-files ceiling must operate during insertion, not only after an unbounded append. Format revision 24, v0.30.0 published, pre-1.0 v0.31 unmerged. All new successes require exact-head results and independent physical/evidence verification; negative controls and full promotion gates remain in force.

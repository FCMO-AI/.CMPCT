# O84 — Bounded opt-in SHA-verified complete VZIP member read (preregistration)

Date: 2026-10-25 UTC. Status: PROSPECTIVE, BEFORE PRODUCT OR TEST IMPLEMENTATION.
Canonical released state v0.30.0 / revision 24 is immutable. This independent candidate is based on exact `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, original Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8` and codec `29526db4203723d83523fc95d074c346b63d7587`.

## Why / source-exact inherited evidence
O81 scientific PR #438 proved with two independent genuine hosted product runs (40193188582 and 40193185335) that an authentic physical copied r24 archive whose VZIP skeleton was changed in a CRC32-preserving fashion returns a different valid ZIP from ordinary `CMPCT.read()` while `verify()` rejects it by the indexed recipe SHA. This is NOT a `verify()` bypass. O79 PR #436 separately owns SHA-authenticated **selective-range** oracles, and PR #274 owns opt-in physical RAW ranges. No current open PR at preregistration owns an opt-in **complete** VZIP member SHA-checking Reader API.

## Narrow primary scientific/product question
Can an opt-in, **budgeted**, single-member `CMPCT.read_vzip_verified(name, *, max_scan_bytes=64*1024*1024)` return the exact immutable bytes that were SHA-checked against the existing authenticated recipe digest, without modifying the ordinary CRC-tier `read()`, `read_range()`, `verify()`, wire format, Builder, codec, native ABI, or normal performance paths?

Mechanism: resolve a target file (optionally a bounded hardlink chain); require storage kind S_VZIP; reject malformed/invalid budget and the stored *logical file length* above budget **before** calling `read()`; read once via the existing implementation, hash the **same bytes to be returned** exactly once and compare with the original recipe SHA-256. No retained verification flag or second full ZIP buffer. The documented promise is *integrity against accidental/physical corruption under the currently committed index/recipe*, not cryptographic origin authentication against an adversary permitted to rewrite the index and recipe SHA.

## Alternative classes BONKed
A. Change default `read()` or `rebuild_vzip()` to SHA-check: would change ordinary CRC-tier runtime/semantics and could incur mandatory release slowdown; requires a separate full official parity court. **Not selected.**
B. Whole-archive `verify(); read(name)`: authenticates unrelated objects, may duplicate reconstruction, and does not bind returned bytes to the verified source under mutation. **Use as stronger cost comparator, not a substitute.**
C. Add r25 authenticated block hashes: real random-range upside, but wire/native/portability carrying cost and overlapping O79 range research are unjustified for full reads. **Not selected.**
D. Explicit same-call indexed SHA over returned bytes, with a logical-byte scan budget and deliberate per-call repeat checking: minimal reversible capability. **Selected.**

## Prediction / stronger control / kill conditions
1. Genuine installed original r24 Reader still returns changed ZIP bytes under O81's same-length, same-CRC32 physical skeleton tamper; candidate ordinary `read()` keeps the original behavior; candidate opt-in read raises `IOError` before returning changed bytes; `verify()` also raises.
2. On unchanged genuine Builder VZIP, opt-in returns the original exact member; supports a real VZIP hardlink alias if the current representation allows it. Both fast `read()` and selected `read_range()` preserve existing behavior and archive bytes/format.
3. A `max_scan_bytes < logical_size` call fails *before* entering `read()` or materializing VZIP. Malformed budget and non-VZIP members must be explicit errors; corrupted/malformed hardlink graphs must not cause unbounded traversal.
4. Paired timing on identical VZIP bytes records normal full read, opt-in full read, and whole-archive `verify()` separately, including CPU/wall and peak RSS when available. First opt-in hash cost is real, never free or folded into baseline. No claim that a one-member file must beat `verify()`; on multi-file archives it should avoid scanning unrelated members.
5. No source identity mismatch, unsupported evaluator weakening, false acceptance, false rejection of valid ZIP, bypass through hardlink alias, or mandatory slowdown of the normal path. Host test must be on installed source outside checkout. Any such violation falsifies the candidate.

## Evidence ladder / scope
Cheap independent code inspection plus inherited O81 physical collision establishes the initial gap. Next: genuine same-source Reader with selected member and physical hostile variant; then portable installed integration and timed negative/positive repeated observations. Generic/full official release CI follows only if candidate merits promotion. A scientific harness success alone does not make a release. Index hashes here are integrity checks, not authenticated signatures. No frozen benchmarks, release policies, thresholds or process boundaries may be changed.

## Concurrency
O81 PR #438 notified in issue comment 6398338109. This is a distinct opt-in full-file API, not O79 selective ranges, O75 Builder publication, O80 Builder fidelity, or O82 Discovery cache. Re-check PR ownership before any late write; no edits to others' branches or shared STATE.json.

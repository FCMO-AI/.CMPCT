# O20 — Extracted PACK bytes versus physical SHA-256 (preregistration)

**Status:** FROZEN PREDICTION, BEFORE O20 PRODUCT-COUPLED RUN.  
**Date:** 2026-10-24 UTC. **Base source:** `FCMO-AI/.CMPCT@2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`, parent PR #258.  
**Research only:** no changes to v0.30.0, r24, stable release or frozen baselines.

## Primary scientific question
Does the ordinary Python `CMPCT.extractall()` publish CRC-repaired, SHA-256-inconsistent S_PACK member bytes despite a source-exact `CMPCT.verify()` rejecting the same archive? This is **distinct** from PR #257/#258, which establish/repair **explicit verify** only. Do not relabel CRC-tier ordinary reads as SHA-authenticated.

## Prior evidence and competing actions
PR #257 independently built revision-24 physical PACK vectors and proved a CRC-repaired mutated PACK passes original strong verify; PR #258 adds one-SHA-per-owner strong verification. A cheapest non-product control is `verify();extractall()`, but it pays a whole-archive scan and cannot protect against subsequent concurrent source mutation. An incremental per-PACK check during extract pays a unique-owner SHA scan, and must be measured before promotion. Default extraction semantics and performance gates cannot be silently changed.

## Immutable prediction
Use the **unchanged** independent `archive_bytes` generator in `benchmarks/v031_pack_physical_sha_court.py` inherited from #257. Make three archives with identical authenticated index grammar: intact shared RAW PACK, one-byte changed shared RAW PACK with **updated CRC32 but stale original physical SHA-256**, and identically changed direct RAW S_BLOB. Expect intact extraction exact, corrupted PACK `extractall` **accepts and publishes the altered member**, corrupted direct S_BLOB `extractall` also accepts under CRC-only normal-read policy. The same source-exact `verify()` must accept intact and reject the mutated PACK/direct (PR #258). Use independent SHA-256 of destination bytes and original/altered source, not `CMPCT.file_sha256` as proof of content.

## Causal discrimination and kill conditions
- If `extractall` already rejects corrupted PACK, **retire** this gap; do not create duplicate implementation.
- If `verify()` accepts mutated PACK on the #258 source, source custody or inherited owner behavior is invalid: stop positive claim.
- If fixture does not actually mutate payload while preserving structure, or correct source bytes do not extract, invalidate court.
- If a proposed strong-extract fix adds CPU, memory, I/O, archive bytes, startup or irreversible semantics, charge them; no promotion on scientific reproduction alone.
- Do not claim adversarial authenticity: an actor who rewrites payload plus all digests can forge internal consistency; source immutability/signer trust is separate.

## Evidence ladder and exit
1. Builder-independent normal/changed complete r24 archives + original physical hash witness.
2. Hosted exact SHA Python Reader, independent extracted output hash and negative classification.
3. **Only after evidence:** choose between explicit `verify()` as documented caller gate, optional strong extraction, or physical-owner-once extraction check; apply full product/release benchmark gate before any promotion.
4. Keep no more than this primary question; do not edit discovery shared STATE without new decision-changing evidence.

## Concurrency boundary
#258 owns explicit SHA `verify()`; #274 owns optional verified RAW **selective ranges**; #351/#363/#367 own **native** extraction/staging; this O20 scientific lane only tests Python **whole-tree extraction** against inherited physical SHA, without changing any owner's implementation.

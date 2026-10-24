# O30 — Concurrent source ABA during a sealed CMPCT archive copy (prospective preregistration)

**Date:** 2026-10-24  
**Status:** FROZEN BEFORE IMPLEMENTATION / RESULT UNMEASURED  
**Scope:** scientific test only; no product/source/format/release mutation.

## Authority, baseline, and primary question

Canonical released CMPCT v0.30.0 / on-disk revision 24; research inherited from #379 at `5994dca7d4d9255a2ed7c6edf1669acf2422e2f1`. O23/#376 proved that `verify(); extractall()` over a mutable source need not bind the physical bytes extracted. O24/#377 and O26/#379 proved a complete **post-copy** immutable disk/memfd source restores the required identity for static post-copy modifications, but explicitly did not evaluate mutation **during** the copy. Those are different trust boundaries.

**Primary question:** Does sealing a completed copy, together with equal source SHA-256 before and after the copy, prove the copy is an atomic image of its source? If not, does the inherited CMPCT strong verifier reliably reject a CRC-consistent, physically SHA-inconsistent copy rather than publish bytes?

## Hypothesis, simpler control, alternative explanation, decision

Prediction: a deterministic source A → fully valid B → A schedule while the copier processes three blocks can produce a sealed hybrid archive H with source `sha_before == sha_after == sha(A)`, stable source dev/inode/length, and `H != A && H != B`. The whole source equals A at the beginning and end. Both complete A and B are independently valid r24 archives; H has an original A physical SHA-256 header and mutated B physical payload. For a stronger causal witness, construct A/B with the **same physical CRC32**, using an independent GF(2) 4-byte CRC compensation, so H ordinary RAW decode succeeds with B bytes, while `verify()` fails specifically with SHA-256 inconsistency. Memfd seals must prevent further writes to H, which do not retroactively make H a consistent source snapshot.

**Stronger simple control:** require a genuinely immutable/trusted source throughout capture, instead of trusting pre/post source equality. A complete post-copy strong verify is necessary before publication; it detects the crafted H but cannot by itself prove provenance against an actor who can rewrite/re-authenticate the whole source.

**Alternative explanation:** the hybrid fails only CRC, structural parsing, or because A/B were invalid; to falsify that, require two valid SHA-verifying A/B archives, same CRC, decodable H with exact B logical bytes, and SHA-specific rejection. The exact source after restoration must independently verify as A.

**Kill/narrow conditions:** If H equals A or B, pre/post source identity changes, A/B fail strong verify, H fails only CRC/structure, H strong-verifies, or H cannot be sealed/read by the inherited Reader, the predicted precise result fails and the episode is marked falsified/ambiguous, not rescued by weakening checks.

**Decision unlocked:** exclude `source hash before == after` and inode/length equality as an atomic-source-snapshot proof when uncooperative same-user writers are allowed; retain immutable-source contract and require copy-result authentication before extraction. This does **not** establish arbitrary concurrent exploitability or that an attacker can defeat strong cryptographic commitments.

## Experiment and evidence rung

- Real revision-24 archive images built from the unchanged, independently authored O23 physical generator, containing 4 MiB RAW logical data.
- Fresh file B has one changed middle-block byte plus a 4-byte GF(2) CRC compensation in the **same copy block**, preserving the CRC of A. Both images have identical index bytes/length and independent correct physical SHA headers.
- Source-owning **separate subprocess** writes B only between copies of first and second 1 MiB blocks, then restores A before the third block. No timing-based race flakiness: an explicit controller chooses the interleaving; the observable models a possible uncooperative writer, not its statistical likelihood.
- Record input/archive hashes, physical-header CRCs and SHAs, initial/final source inode/length/hash, memfd seal bits, per-block copied SHA identities, hybrid SHA, ordinary read bytes, exact verify failure, output non-publication, and extra N-byte memory/copy I/O lower bounds.
- Independent controls: unmutated clone A extracts A; standalone B verifies and extracts B; fresh source after ABA verifies/extracts A; sealed H declines verified extraction.
- Source identity and result-bearing CI are pinned to exact Git heads and immutable inherited code blobs.
- Scientific rung: adversarial causal falsifier + hosted exact-source reproduction. No end-product/benchmark speed or general platform claim.

## PARETOBONK, concurrency and scope

Other candidate work: merge/prioritize existing Reader fixes (#381/#383), redesign a per-owner streaming verified extractor, or perform cheap proof of O26's copy-time caveat. The latter tests a release-relevant trust assumption without altering contested product code, avoids duplicating existing hardlink owners and exposes whether a tempting hash-before/after shortcut is a false guarantee. PR #379 owns post-copy kernel seals; this independent extension owns only source-ABA **during copy**. `docs/discovery/STATE.json` remains staleable and is not a lock. Do not alter other PRs, frozen tests, release gates or discovery policy.

**Expected no-product-change outcome:** scientific evidence, not a new release, not stronger source provenance, no proof of safe destination publication, cross-platform portability, RSS scalability or performance. Preserve all negatives and exact-head pending states.

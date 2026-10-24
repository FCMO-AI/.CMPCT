# O20 — Ordinary extraction CRC tier vs physical PACK SHA (hosted result)

**Date:** 2026-10-24 UTC. **Scientific decision:** `EXTRACT_CRC_TIER_CAN_PUBLISH_SHA_INCONSISTENT_BYTES`. **Product fix:** NOT IMPLEMENTED. **Promotion:** NONE. Released CMPCT v0.30.0, on-disk r24, and existing normal-read/strong-verify contracts remain unchanged.

## Source, authority and preregistration

- Exact inherited candidate: PR #258 `2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`, which adds explicit one-per-owner physical SHA verification; this experiment does NOT alter its implementation.
- Falsifiable prediction precommitted as `docs/v031-research/PACK_EXTRACT_PHYSICAL_SHA_O20_PREREG.md` in **`f62263aad97f87b1eb8819a40e3b6ed0044ff886`** before introducing the new court.
- New court source: `benchmarks/v031_pack_extraction_sha_boundary_o20.py`, committed at `9c15075012a6d20f4d62a26ac3877cce53b638e0`.
- Frozen independent physical-r24 fixture generator from #257 (unchanged Git blob `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`).
- **Result-bearing exact-source HEAD `9b86ac1f85e8273c44f69a11ef773510419be41b`.**
- [Hosted GitHub Actions run 40116605456](https://github.com/FCMO-AI/.CMPCT/actions/runs/40116605456): specialized `physical-pack-extract` job **SUCCESS**, installed `cmpct-0.30.0` package built; source and unchanged baseline oracle Git blobs checked before the court.
- [Artifact 12570190167](https://github.com/FCMO-AI/.CMPCT/actions/runs/40116605456/artifacts/12570190167), uploaded ZIP SHA-256 `da6b065fc886ff56d795045fc458e529069cd540358908ec7da4e8c389358fcd`; contains raw `o20-extract.json`, inherited `verify` control, and source-fingerprint witnesses.

## Measured decisions (three complete real CMPCT archives)

The original physical content is **128 bytes**. The mutant changes exactly its last byte and recomputes **only CRC32**, preserving the stored original physical SHA-256. The original and mutated shared-PACK archives both measure 628 stored bytes; the independently constructed direct-RAW control measures 586 bytes. Primary index and structural preflight remain valid.

| Full archive | Exact `CMPCT.verify()` | Ordinary `CMPCT.extractall()` | Actual published bytes |
| --- | --- | --- | --- |
| Intact RAW shared `S_PACK` | **ACCEPT** | **ACCEPT** | **Original, byte-exact** |
| CRC-repaired mutant RAW `S_PACK` | **REJECT** | **ACCEPT** | **Mutated, SHA-inconsistent** |
| CRC-repaired mutant direct RAW `S_BLOB` | **REJECT** | **ACCEPT** | **Mutated, SHA-inconsistent** |

Independent filesystem output SHA-256:
- Original (including intact PACK output): `0706044ad714888dc1bfeac538023ac15c129046e0382e82c257c27fb8795794`.
- Mutated output for both corrupted PACK and direct BLOB: `d36fdb237035c73b8127de8566ca2ce89f187bdf816c02f37ea9fbec700cf8ab`.
- Mutant shared PACK archive SHA-256 `503cc736e23a90946048591fc324b14431099826202fd87c96b3e5193a447b41`.
- Intact shared PACK archive SHA-256 `a3c10347fbaacaf78ee264ff02b6aa86ff4c463f0565be94903fc7010411ebac`.

The shell's independent assertion `O20 research negative precisely reproduced` printed in the completed hosted job. Both mutated output hashes differ from the unchanged physical record SHA-256, not merely a renderer's label. Source and action logs confirm actual installed Python product execution.

## Causal explanation and alternative controls

Ordinary `CMPCT.extractall()` delegates packed and direct members to `CMPCT.read()`, which uses the existing cheap physical CRC32 tier. The corrected `CMPCT.verify()` instead checks the original SHA-256 commitment of each physical PACK owner once; direct files compare to their physical SHA. This experiment proves a **differentiated operation contract**, not a regression in `verify()` nor a newly demonstrated exploitable attack.

Alternative `verify();extractall()` uses the existing strong verification but repeats reads/work and still does not freeze mutable source state between operations. A product-level strong extraction path would need to authenticate physical owners **as it materializes** and stage verified data before publication, with complete coverage for all representations, not simply add a PACK-specific check while direct RAW remains unchecked. Do not promote a narrow helper as a general authenticated filesystem extractor.

For external context, CPython's documented ZIP `testzip()` checks member CRC and headers; an internal CRC/SHA tier choice must not be misrepresented as external origin authentication. Reference: https://docs.python.org/3/library/zipfile.html.

## Costs and self-critique

- This 128-byte RAW physical fixture is intentionally a **binary causal falsifier**, not a realistic compressed PACK performance or exhaustive filesystem benchmark. A held-out Zstd-packed Builder-produced corpus is needed before attributing generic coverage.
- Hashing each 256 KiB physical owner necessarily adds a sequential SHA input pass and CPU/memory traffic, although a <=2 MiB cached `_blob()` may avoid a second decompression. Direct physical frames, large owners, cache eviction, source mutation and output staging impose separate costs.
- Illustrative **local CPU-only Python SHA** microdiagnostic, **not product/runner evidence**: 256 KiB median 0.148 ms per SHA; 16 MiB median 9.443 ms (7 small repeated batches, environment-specific). Full product wall/RSS/create/extract, cumulative hashing, portability and official ABBA **UNMEASURED**.
- Three positive experimental assertions under tiny fixed data do **not** establish active adversary reachability, media durability, hostile destination safety, crash rollback, signed provenance or full trustworthiness of arbitrary archives. A party who rewrites a payload, CRC32 and original SHA-256 consistently can make an internally valid archive without an external trust root.
- A direct source inspection already strongly predicted this result. Hosted execution supplies source-exact external evidence and independent output identities, but the information gain is **narrow**; do not repeat near-identical variants without a new decision-changing question.

## Concurrency / release / next decision

Current separate product ownership remains #258 (strong explicit PACK verification), #274/#277 (optional verified RAW selective range), and #351/#363/#367 (native extraction/staging). No Reader, Writer, Builder, format, ABI, benchmark, evaluator, threshold or Discovery shared STATE file changed by O20. **No merge or release credit.**

**Decision:** O20 scientific hypothesis CONFIRMED for precisely the three tested representations. The **next highest-leverage product fork** is a design-level comparison: continue documenting CRC-tier default plus explicit `verify()` versus a **full-representation** strong extraction/verification-and-staging contract (one physical owner authentication, bounded memory, safe publishing). First use one held-out compressed shared owner and a control where SHA verification must prevent publication, then charge complete real-product economics and owner integration. Do not spend on more tiny RAW fixture variations.

Subsequent documentation-only commits after the result-bearing HEAD require their own exact-head checks before describing the *new final HEAD* as fully green. This result is bound to the source-exact hosted run above.

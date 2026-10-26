# O198 — Authenticated r24 sparse extent-length causes selective-read divergence

Date: 2026-10-26 UTC.
Status: **DECISIVE NEGATIVE PRODUCT BEHAVIOR ON AN UNMERGED READER LINE; NO PRODUCT FIX OR PROMOTION**.
Owner of this independent falsifier: [PR #532](https://github.com/FCMO-AI/.CMPCT/pull/532).
Canonical release remains v0.30.0 / physical format revision 24; candidate Reader source O193 #521 remains unchanged.

## Original prospective test and source custody

Preregistration was committed **before** code/experiment at `8338a81b180e30b3e218a4cee0f9fdc172f2aefb`.
Scientific instrument committed at `3b75a04f4b713a57e1d31acbff2521cb052b40ee`.
Original successful result-bearing PR HEAD: `6c1dda1425582e9b7081126538e736c4666f62d4`.
All native jobs installed exact CMPCT independently from source, checked product source file bytes and git HEAD, and verified that there were no changes in `src/`, `native/`, `tests/` or `benchmarks/` relative to O193 source HEAD `392112ce859db5a7f85be593c82d1cabc1f5131f`.
Reader Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`.
Court Git blob `056b5e5e2c10eae820678e08e0aeae81d9a6e324`.
Prereg Git blob `1173aa51ab3c87835cec94cdb0656d857c2a4be6`.

**Result-bearing native run:** [GitHub Actions #40380919379](https://github.com/FCMO-AI/.CMPCT/actions/runs/40380919379).
Ubuntu 24.04: SUCCESS, macOS 14: SUCCESS, Windows Server 2022: SUCCESS.
Three installed Readers returned `REPRODUCED_AUTHENTIC_SPARSE_RANGE_SEMANTIC_GAP`; scientific job success means the defect reproduced, NOT product approval.

Source-verified artifact IDs:
- Ubuntu `12679022118`, artifact ZIP SHA-256 `c582b697c8516340c71662973f49914a6b11d49cf55c04f536b524cc61925304`.
- macOS `12677274551`, artifact ZIP SHA-256 `de5646e559b5bae9fca05f5207f9e21805545431a8d8f54f07f5695464aa229e`.
- Windows `12678092342`, artifact ZIP SHA-256 `e6cf77b2916f216d2f0d306077faed202430af32ae6e4f6961349561581688fc`.

All twelve physical CMPCT files in three hosted jobs were independent native reconstructions of four deterministic, fully serialized 456-byte r24 archives. Primary and tail MessagePack/Zstd index copies and index SHA, RAW blob CRC/SHA, logical full-file SHA, archive SHA and actual installed Reader identity were verified. Each variant's archive SHA matched across all three platforms.

## Decisive control matrix

Content is four ASCII bytes `ABCD`; whole-file SHA-256 is `e12e115acf4552b2568b55e93cbd39394c4ef81c82447fafc997882a02d23677`.
Each archive differs only in the index's sparse extent declaration `[off=0, ln=..., blob_refs=[0]]` and necessarily its recomputed index/digest bytes. Blob data, declared logical file size `4`, and whole-file SHA remain identical.

| Declared `ln` | Real blob bytes | `verify()` | `read()` | `read_range(0,4)` | `read_range(2,2)` | `extractall(metadata=False)` |
|---:|---:|---|---|---|---|---|
| 4 (valid control) | 4 | PASS | `ABCD` | `ABCD` | `CD` | `ABCD` |
| 1 (underspecified) | 4 | **PASS** | `ABCD` | `ABCD` | **`00 00` (wrong)** | `ABCD` |
| 2 (held-out underspecified) | 4 | **PASS** | `ABCD` | `ABCD` | **`00 00` (wrong)** | `ABCD` |
| 5 (overspecified) | 4 | **PASS** | `ABCD` | `ABCD` | `CD` | `ABCD` |

**Result:** one self-consistently checksummed revision-24 archive can pass full logical verification and extraction, yet a subsequent selective read returns bytes different from the verified content. The index digest is an integrity checksum, not an external trusted signature; an adversarial archive creator can author internally consistent malformed length metadata.

The source mechanism is causal: `read()` and sparse `extractall()` iterate referenced blobs using their actual sizes without comparing total bytes to the declared extent `ln`; `read_range()` filters by `extent_end=off+ln` and thereby wrongly skips the still-present raw blob for a late selective request. This is a **range-specific semantic inconsistency**, not a demonstrated mutation of honest Builder-created sparse files.

## Independent receipt audit

The three original artifact ZIPs were downloaded and audited independently without importing CMPCT. For each host the auditor verified exact Git HEAD, Reader/court/prereg Git blob identities, complete artifact manifest, four archive SHA identities, every positive control, both negative range outputs, and byte-for-byte extracted SHA. All three hosts agreed on all four variant archive hashes.

Independent source script SHA-256 `8f6efde708e3e44de3d1cdec6bb3c967776e0d99ab34a67fc4b21b62a74391b9`; result JSON SHA-256 `072c7eacc1d409ed178cf45018e00e109c45574816b4621f10d27c71d938fdf4`.
These supporting files are local audit artifacts for this activation; durable scientific source and 3-host raw evidence remain the GitHub PR/workflow/artifacts.

## Decision, alternatives, and strongest negative/self-critique

**FALSIFIED:** "index verification and full read necessarily guarantee sparse `read_range()` reconstructs identical selected bytes for arbitrary self-consistent r24 indexes."

**NOT PROVED:** a malicious archive can change original CMPCT archive bytes after verification without detection; source has no trusted signing contract here. No remote exploit frequency, Builder-generated malformed corpus, existing canonical release impact measurement beyond shared source lineage, ≥4 GiB performance penalty, memory/recovery safety, or universal parser claim. The four inputs are deliberately tiny and adversarial.

**Cheapest plausible production invariant:** before accepting sparse geometry, validate `ln == sum(referenced blob declared uncompressed lengths)` and require each extent to fall within logical file bounds; further sortedness/overlap law must be reconciled with historical compatibility before promotion. Prefer one bounded open/index validation to a per-`read_range` scan that would worsen the O194/#522 `E × Q` cost. Validation is prospective design only: no implementation or benchmarks have earned adoption.

**Independent future fork:** owner O193 #521 should reuse this exact hosted court, add a minimal strict geometry admission check, run valid real Builder profiles and existing extraction/ZIP64 controls, then measure index-open cost and heterogeneous hostile inputs. Do not weaken the full SHA or reinterpret a malformed archive as a new valid format revision.

## Concurrency, Discovery Engine and release

No ownership collision or extra version consumed. O193 remains sole ZIP64 Reader owner, O194/#522 sparse performance work is separate, O195/#524 rejected indexed product promotion remains unchanged. Discovery `STATE.json` not rewritten; no general discovery-policy edit is warranted by a single mechanism. Best counterfactual early discriminator: cross-check descriptor geometry against referenced blob sizes *before* assuming "whole-file SHA verified" implies selective-byte equality; do not substitute an in-memory mock for actual serialized Reader evidence.

Engineering Evidence/Version Discipline/CI topology/General tests have **separate** exact-head CI truth, not inferred from this green science court. A later document-only HEAD requires its own CI observation. **No merge, no release, no canonical product patch.**

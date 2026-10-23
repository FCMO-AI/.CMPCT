# v0.31 — large-offset ZIP64 sparse metadata oracle (preregistration)

**Date:** 2026-10-23. **Tier:** research / interoperability metadata oracle only. **Status at preregistration:** UNEXECUTED.

## Authority and collision check

Development source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; published v0.30.0, canonical r24. PR #260 owns *count-only* ZIP64 product code: exact head `333bea363fc4583abd1a1f33b68f20d2e07ba179`, and explicitly delegates >4 GiB offsets/member sizes to `zipfile` fallback. This independent court **does not edit the Reader or PR #260**. It asks an adjacent wire-format question, not a duplicate owner implementation. PRs #269/#272 own destination extraction security; #273 owns sparse extraction hash performance. This experiment changes neither.

## Question, baseline and falsifiable hypothesis

Can **a real ZIP64 archive** encode (a) an individual STORED member larger than the 32-bit field and (b) the *following* small compressed member at a physical local-header offset > 4 GiB, while preserving exact small-member extraction in mature readers, with bounded RAM and negligible physically allocated disk blocks? Can that compose with >65,535 central-directory entries?

Current fast `Reader.export_zip` writes count-only ZIP64 records in PR #260 but conservatively falls back to `zipfile.ZipFile.writestr(self.read(rel))` when projected member size or central offsets exceed 32 bits, potentially materializing a whole large member. This is not a proven OOM: it is a source-visible unbounded allocation path and a real unresolved interoperability-economics question.

**Prediction P1:** The PKWARE v4.5 structures permit an archive with a >4 GiB STORED sparse member, a later small independently readable compressed member with ZIP64 **offset-only** central extra, and ZIP64 EOCD/locator; CPython `zipfile` will parse both entries and exactly extract the small payload without materializing the giant member.

**Prediction P2:** A deliberately corrupted late-member ZIP64 header offset is rejected (negative integrity/control; checksum of the giant sparse member is calculated correctly even if not fully read during the court).

**Prediction P3 (optional if cheap):** The same wire behavior coexists with count overflow >65,535 (separate from PR #260's count-only source).

**Strong simpler control:** An all-ZIP32 small archive is already supported by PR #260 and Python `zipfile`; it cannot represent a true >32-bit local offset or member length, so a size-only threshold / 32-bit wraparound is an invalid substitute. Another simpler product alternative is streaming a valid ZIP through stdlib `ZipFile.open(...,'w')`; its memory and Deflate-copy implications must be measured separately.

**Alternative explanations/falsifiers:** CPython may interpret a giant sparse prefix as concatenated junk or silently correct a malformed offset; independently inspect ZIP64 bytes and independently read the small member, then tamper only the committed offset to see whether it is actually honored. Any failure of second-member extraction, archive structural consistency, source identity, or false-negative tamper control narrows/kills this exact metadata oracle.

## Resource and semantic boundaries

- Construct sparse-file members with `seek` on a temporary Linux filesystem, no 4 GiB Python allocation or 4 GiB write. Maintain correct CRC32 of conceptual zero payload via bounded slab loops.
- Validate the `st_blocks` physical allocation and refuse to label any storage win when sparseness is unsupported.
- Real large data *reading* is deliberately unmeasured; validate only central metadata and the small member's decompression/CRC/bytes using `zipfile` and, when present, an independent Info-ZIP tool.
- Record logical archive length, physical allocated bytes, create wall/CPU/RSS, source SHA for the script, and exact interpreter/runtime.
- This synthetic ZIP is **not an archive made by CMPCT**, no product throughput/size/security/portability evidence, and no native-Reader/API claim.
- Do not mutate CMPCT archive format, frozen benchmarks, comparator semantics, release thresholds, `STATE.json`, or the canonical ZIP exporter.

## Decision rule

**PASS:** metadata feasibility with bounded fixture materialization; advance a *separate* prospective product engineering cost study if product owner #260 wants larger-offset support. **FAIL:** distinguish malformed oracle construction from actual format impossibility before retiring; preserve the negative. Independently report every unresolved requirement: native emitted ZIP64 records, direct Deflate reuse, recovery, full CRC over giant members, streaming memory, Unix/Windows ZIP tools, and complete CMPCT input semantics. No release credit.

## Standards basis

PKWARE APPNOTE ZIP64 extra-field rule (only saturated 32-bit fields are replaced, in fixed order) and mature CPython zipfile implementation. The original source/version and output fixture checks are preserved in the instrument, not inferred from a web summary.

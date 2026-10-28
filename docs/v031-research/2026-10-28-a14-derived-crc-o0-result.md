# A14-O0 — Exact derived-field elimination: first bounded oracle result

Date: 2026-10-28 UTC  
Status: **O0_STRUCTURAL_HEADROOM_ONLY**, local independent replay PASS; **not a CMPCT product result, not merge/release ready**.

## Authority and freeze
- Parent: published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / revision 24.
- Prospective prediction: `docs/v031-research/2026-10-28-a14-derived-crc-o0-prereg.md`, frozen **before code** in commit `243c348762813444d7a9c5a2bc10b3a06fe2b7ea`.
- Only standalone research source and evidence were added. No changes to CMPCT Reader/Builder/native, format, published benchmark, historical receipts, CI evaluators, discovery state or policy.
- Source identity: `research/a14_derived_crc_o0.py` SHA-256 `f6f5fb61afb4549f6f1afc248b1418a396bc6756676a44b039791ad9ed289262`; reference referee SHA-256 `d7ed51defa323bdbd39d845ccd08d7b91fe91a6f8d544c312f31aff0e8d65fc2`.
- Execution environment: local Linux, Python 3.13.5, `zstd --version` recorded with the raw result; CPU/wall are single-pass exploratory figures and cannot be promoted to stable product economics. GitHub Actions Ubuntu/Python3.11 exact-head replay is a separately dispatched research check, not automatically green.

## Worldview delta, mechanism and comparison
**Assumption A14:** generic opaque byte streams can contain fields that are exactly computable from other bytes, not merely redundant adjacent content to be compressed statistically. A bounded content-only candidate scan searches fixed record strides 16..256 (step 4), checksum offset `0`, `4` or last 4 bytes, and little/big endian CRC32, then checks **all** records before admission. The experimental decoder stores exact width/offset/endian/count, SHA-256 of original full bytes, compressed body size, and Zstd-19-compressed body (without stored CRC bytes); it **recomputes** each field to reconstruct original bytes exactly and verifies the charged SHA. CRC32 is *not* treated as a cryptographic authentication or as object identity.

Controls operate on precisely the same input: full solid Zstd-19, full XZ/LZMA-9, and a fully reversible stride transpose + Zstd-19 with 12 extra parameter bytes. The final comparison chooses the **strongest measured** of those three; all representation header/decoder-visible facts are charged. Complete folded artifact header: 61 B, no gifted checksum facts. Candidate generation/discovery was not counted as a free product operation; instrument records its wall time, while the bounded **search grammar** is the O0 gift.

## Measured local complete-artifact sizes

| Synthetic regime | Input bytes | Folded bytes (header included) | Strongest unchanged-input control | Control bytes | Exact reduction |
|---|---:|---:|---|---:|---:|
| High-entropy 36-B records; CRC head | 294,912 | 262,221 | Zstd-19 | 294,931 | **11.090730%** |
| High-entropy 68-B records; CRC tail | 278,528 | 262,221 | Zstd-19 | 278,547 | **5.861129%** |
| High-entropy 132-B records; CRC offset 4 | 270,336 | 262,221 | Zstd-19 | 270,355 | 3.008637% (**below 5% materiality**) |
| Structured 68-B records; CRC tail | 278,528 | 1,309 | Transpose + Zstd-19 | 2,246 | **41.718611%** |

The two high-entropy 36/68 width-and-position variants satisfy the preregistered different-regime >5% criterion. The structured case independently passes the strengthened transposition control. The 132-byte high-entropy case is a positive *byte* result but not a material >5% win; retain this negative threshold result as representative of the declining fraction `4 / record_width`.

Three adversarial negatives were **rejected**, not classified as checksum-positive: no-CRC random contents, CRC bit flip only in the final record beyond the 32-record sample, and alternating checksum offset. Every positive was reconstructed **byte for byte** and matched its original full SHA-256. Every tested materialized artifact rejected six malformed/corrupted forms (magic, offset, compressed length, SHA, truncated bytes, altered compressed payload).

## Independently rooted referee and limitations
The separate `research/a14_independent_referee.py` does **not import** the experiment code. It regenerates all seven deterministic corpora, builds independent checksum-free representations and reversible reconstructions, recomputes each conventional comparator and decision, verifies original/derived SHA-256, and deliberately corrupts six receipts: all six are rejected. Local result: `referee=PASS`, `positive_cases=4`, `negative_controls=3`, `strong_distinct_regimes=2`, `decision=O0_STRUCTURAL_HEADROOM_ONLY`. The independent referee does **not** independently validate wall-clock timing; the source-linked sizes, bytes, digests and experimental admissions are its actual proof surface.

**Main counterargument:** these are planted synthetic CRC relationships. They prove capability/headroom under a content-detectable special structure, not prevalence, generic admission cost, naturally occurring held-out transfer, or a net archive-level product win. The tested search grammar is gifted to the scientific oracle, though all decoder-visible representation facts are charged. In the high-entropy 36-byte case the local fold compression step itself measured roughly 249.6 ms, versus 118.5 ms for full Zstd-19, **before adding discovery**; this already demonstrates real product-speed debt in the same-input test. The 68-byte tail case is near parity in this one measurement. Timing variation is not statistically resolved by a single invocation.

This O0 cannot claim selective-read locality, independent chunk units, physical archive bytes/index/dedup/recovery, RSS, cold startup, cross-host Python+Zstd parity, mutation safety, read-only native portability, licence/ABI integration, official benchmark improvement or release readiness. Decoder SHA prevents falsely accepting wrong reconstructions in this toy artifact, but is not a drop-in replacement for CMPCT's existing integrity/recovery contracts.

## PARETOBONK decision and future leverage
Compared alternatives: (1) continue saturated VZIP per-call loop optimization (multiple recent negative installed-Reader courts), (2) repeat active S_CHUNKS native/read recovery work owned by other activations, (3) add speculative generalized format/reader primitives, and (4) run this bounded, distinct A14 proof. The cheap A14 O0 changed one scientific possibility: **derived field values can be inferred and omitted exactly, not only compressed as bytes, with an explicit charged decoder program**, but only for discoverable, provable checksum records.

**Next cheapest discriminating action:** use a **held-out naturally occurring binary record collection**, with provenance and legal/public-shareability vetted, to test prevalence and false-positive safety under the unchanged general detector, before changing any production codec grammar. Alternatively run a stronger general-purpose transform/entropy control on the same inputs to narrow byte headroom. A positive that survives these checks may justify an O1 charged installed/archive-level admission bound and selective access cost. A real-world prevalence negative should park the family, not spawn CRC placement thresholds.

**Counterfactual:** the maximal removable data fraction for random records with a 4-byte derived field is ~`4 / width`, less header cost; thus 132-byte random records cannot plausibly reach a 5% raw-byte saving through deletion alone. This is a prospective, low-cost kill for the *high-entropy long-record* regime. Record locally; it does not justify self-modifying Discovery policy from one oracle.

## Handoff
- Product: **unchanged**.
- Scientific result: positive under frozen synthetic scope; 132-byte materiality negative; external validity and product economics unresolved.
- Concurrency: no collision found with a pre-existing A14 derived-CRC owner; O74 #430 only proves CRC metadata cannot authenticate identity. Discovery STATE is under separate PR #574; left untouched.
- Evidence: local raw JSON and independent-referee JSON; hosted CI results must be reconciled to its exact source HEAD and artifacts separately when available.
- Promotion: **no merge, no release, no numeric version or format bump**.

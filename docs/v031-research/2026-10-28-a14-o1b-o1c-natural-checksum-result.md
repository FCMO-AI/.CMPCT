# A14-O1b/O1c — natural checksum-container result (2026-10-28)

**Decision: PARK the tested PNG/GZIP derived-checksum representation for CMPCT product integration.** This is *negative natural-data scientific evidence*, not release/product benchmark evidence and not a universal impossibility proof. Parent A14-O0 [#670](https://github.com/FCMO-AI/.CMPCT/pull/670) remains a scoped synthetic structural possibility, with its original 0/672 natural windows left intact. Child [#673](https://github.com/FCMO-AI/.CMPCT/pull/673) owns this independently scoped next rung. No Builder/Reader, on-disk format, benchmark thresholds or discovery policies changed.

## Exact source and preregistration

- O1b prediction committed **before the instrument and any corpus inspection** at `5ffbffb3096d1134583daea3dcbaf1e9e919b7d0` ([prereg](2026-10-28-a14-o1b-natural-checksum-prereg.md)).
- Original source Git blob `e3506865b1429b745d434d73c8bbcbe9eafd9ecd`; file SHA-256 `ed3908d63629ee56842481d1f6880aea93cfe6e4ca3203bfd4721ad48f0d9906`.
- Independent third-root referee Git blob `188c629b8a67fd206019275ba23eca18b8904650`; file SHA-256 `63dbdff3a35cb4277ad6efcdc925cd52ec6ed507d3c477464e5dc339466ec903`.
- O1c stronger codec-symmetric experiment was **preregistered after O1b evidence but before O1c execution** at `4de5fa28a8a70cd4e868bc487a6f722c9f691e75` ([prereg](2026-10-28-a14-o1c-symmetric-codec-prereg.md)). O1b is not retroactively reinterpreted as a test of all codecs.
- O1c source Git blob `e42d2a25a99a8323f99189a541e908efe87010dc`; file SHA-256 `72fe50625047ccf9b5eee034fb1a598cfe9ba3703f554319c0cfef178a92b8a0`.
- O1c independent arithmetic/provenance referee SHA-256 `9ffea94341460340c40271ca0a4ec3e29da49059ba03e405e80e66df572cd953`; source matches repository research script (compare current blob SHA).
- Exact source selection: first 64 *different source content SHA-256 identities* each among deterministically path-hash-ranked natural PNG and GZIP files under /usr and /opt on the instrumented Linux host, size 256 B through 1 MiB. No cherry-picking by outcome, source payload upload, filename disclosure, or sample replacement. **64/64 valid and exactly reconstructed in each family**; held-out natural but host-distribution-specific.

## O1b measured full artifact (Zstd-19 after CRC deletion)

| Natural format | Original bytes (64 files) | Bytes of CRC/ISIZE fields | Strongest direct codec bytes, per file | 57-byte-header candidate bytes | Complete size difference |
|---|---:|---:|---:|---:|---:|
| PNG | 443,634 | 1,696 | 426,050 | 434,417 | **+8,367 B / +1.964% worse** |
| GZIP | 1,541,265 | 512 | 1,446,789 | 1,461,865 | **+15,076 B / +1.042% worse** |

The direct baseline is the *minimum* among Zstd-19, XZ-9, Brotli q11 on **the exact original bytes**, chosen independently per file. The candidate fully stores magic, format, length, encoded size, original SHA-256 and compressed CRC-free content; restored bytes verified exactly for every input. No file in either family crossed the preregistered **5%** positive materiality bar. Brotli won 56/64 direct PNG controls and 56/64 direct GZIP controls.

Source-locked O1b raw JSON SHA-256 `9a1ff2449a1a4d80f8939076143962f042833b2a5f55cf453e6066dccb75a4a2`. Independent **source-file rescan + all 128 raw SHA identities + recompression of every candidate and all 384 direct controls** reconciled exact bytes, hashes, sizes, CRC fact counts, summary and decision; referee PASS, **6/6 forged receipts rejected**. First referee version falsely treated equal compressed sizes as requiring a unique codec name because sorted JSON keys changed tie ordering. That *evidence-tool failure* was fixed by accepting any control tied for minimum; no candidate, comparator, data or threshold was touched. Preserve this negative about evidence comparators.

## O1c: stronger symmetric codec candidate

To attack O1b's asymmetric candidate choice, O1c tried **Zstd-19, XZ-9 and Brotli q11 after CRC removal** with exact roundtrip on every codec, all decoder facts and a fully charged **58-byte** header including codec selector. The *direct controls and source identities remained identical*.

| Natural format | Direct best size | Best per-file CRC-folded codec, fully charged | Complete size difference | 5%-positive files |
|---|---:|---:|---:|---:|
| PNG (64) | 426,050 B | 427,768 B | **+1,718 B / +0.403% worse** | **0** |
| GZIP (64) | 1,446,789 B | 1,449,916 B | **+3,127 B / +0.216% worse** | **0** |

Candidate encoder-search CPU/wall is **not free**: summed measured wall of the three candidate codecs was **9.709 s** for 64 PNGs and **12.096 s** for 64 GZIPs, excluding enumeration and direct-control work. Selected-mode decoding additionally accounted for 50.5 ms / 49.8 ms respectively, on this host. These are local sums, not calibrated full-product benchmarks or peak RSS.

O1c raw JSON SHA-256 `50df346271c8e3fa3299c80a15dbdbf3f4dd5caec90d695456089e7ee459748d`. An independent 128-row source/size/ratio and three-codec-choice referee bound the O1c receipt to the O1b SHA, checked all minima and aggregates, and rejected **6/6 changed receipts**. Result `PARK_FORMAT_CHECKSUM_FAMILY` survives the stronger symmetric codec.

## Counterfactual: could shared metadata alone rescue the family?

Very favorable, unimplemented **one 58-byte header per entire 64-file family** removes 63 of 64 per-file headers, with all other measured codec bytes frozen. This is *not* a deliverable archive (file segmentation/codec identity/digest metadata are now gifted for free), but a useful upper-rung counterfactual:

- PNG: 424,114 B candidate versus 426,050 B direct; saving **1,936 B / 0.454%**, still below the **1%** aggregate advancement criterion.
- GZIP: 1,446,262 B candidate versus 1,446,789 B direct; saving **527 B / 0.036%**, far below the criterion.
- If even the last header is gifted, the maximum measured-stream gain is **0.468% PNG / 0.040% GZIP**. This is a bound *for the measured compressed streams*, not for every conceivable new representation or cross-file transformation.

The pre-observable natural data regime already signaled low carrying capacity: only **1,696 B of CRC over 443,634 B PNG input** (0.382%) and **512 B over 1,541,265 B GZIP** (0.033%). O1b's per-file 57-byte header and O1c's 58-byte codec/header typically dominate. Different codec selection narrowed the loss but did not reverse it. The transferable prospective lesson is **charge bytes of derivable information against the minimum decoder-visible proof/selector overhead before building a new grammar**. Do *not* self-modify Discovery Engine policy on one bounded format-family study.

## Correctness, safety and limitations

Every accepted natural source passed original PNG CRC / gzip footer validation and exact binary reconstruction. Selftest: two generated positive roundtrips; six tampered candidate artifacts rejected; corrupted PNG and malformed/concatenated GZIP refused. The independent O1b referee recalculated exact hashes for every input, candidate and conventional control; O1c independently audited numerical claims. Tests are not proof of hostile input handling in a packaged Reader. In particular, the research subprocess decoder does **not** establish peak decompressed-output memory limits for arbitrary adversarial Zstd candidates; never promote this parser. CRC32 is not cryptographic authentication. GZIP reconstruction requires a full bounded inflate; PNG's CRC does not.

The natural host corpus is a sample of installed public software assets, **not a complete universe or independent cross-platform experiment**. File-content hashes are durable in raw local receipts; source files themselves are not committed. A repository CI workflow separately executes exact-head source integrity selftests and a hosted Linux natural-corpus rerun with uploaded raw results if the runner can supply the corpus. Hosted environment is different and must report its own manifest, not impersonate these local identities. Official CMPCT Builder, Reader, release/frozen matrix, competing archive semantics, RSS, I/O, selective reads, platform codecs and generic admission remain unmeasured.

## Decision / next leverage

**No merge or release. Do not add a PNG/GZIP checksum deletion grammar.** The A14-O0 synthetic seed remains historically valid for dense high-entropy fixed-width records. A14 as a near-term general product family is **PARKED** pending independently observed natural dense record populations with per-record derived-information density enough to amortize header, search and decoder cost. Reopen on a material *new format/data regime or representation ownership* and an inexpensive mathematical charged ceiling, not another codec/threshold variation of these PNG/GZIP files.

The next distinct high-leverage route remains product correctness and safe Reader/source custody or a different information representation with broad natural data availability. Leave other owners (#662, #653, #574 and recovery) untouched.

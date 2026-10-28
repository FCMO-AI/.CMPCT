# A14-O1b — Natural checksum-container oracle, preregistration (2026-10-28 UTC)

**Status: FROZEN BEFORE NEW INSTRUMENT / RESULTS.** Child of A14-O0 owner PR #670 at exact source `e3f9a3f965616dba31054ba71b9ee610a8f8dbea`. Independent **format-family generality falsifier**, not a rewrite of the fixed-stride detector, not a product implementation, release, or alternate project-state database. Parent #670 unchanged.

## Question and alternative frames

A14-O0 demonstrated large exact CRC32 field folding on planted fixed-stride high-entropy data; its held-out OS O1a admitted zero ordinary windows. A different, stronger setting is **real checksum-framed containers**, where checksum positions are discoverable from documented generic structure rather than planted aligned 16..256-byte fixed records. Ask whether the same idea has economically material byte headroom on natural *PNG* and single-member *GZIP* files, even gifting the experiment an exact format discriminator. The direct no-transform conventional compressor wins whenever folding loses; the format grammar is not proposed as generic CMPCT detection.

Two independently rooted families:
- PNG: zero-copy parse and verify chunk framing and existing PNG CRC32 over chunk type + chunk data; remove each four-byte CRC, then exactly regenerate from the preserved length/type/data during decoding; never decompress IDAT.
- GZIP: accept only a single correctly authenticated member; remove existing CRC32 and ISIZE footer (eight bytes), then regenerate them by bounded full Deflate decoding. Charge the extra full decode work. Concatenated or invalid files are refused, not repaired or silently dropped.

**Host corpus selection frozen before outcome:** enumerate regular `*.png` and `*.gz` under `/usr` and `/opt` on the available Linux host, exclude symlinks, files <256 B or >1,048,576 B, order candidates by SHA-256 of their path string and take at most 64 distinct SHA-256 content identities per family; no content/outcome-based resampling. Parse refusals count against selection coverage; no backfilling. Do not commit raw source bytes or private paths. Persist only SHA-256 hashes, content lengths, stable anonymized record IDs, aggregate input counts and tool versions. This is a host-specific natural held-out sample, not a representative universal corpus.

## Controls, measurements and predeclared decision

For every supported input compare complete candidate `[magic, format-id, original-size, compressed-length, original SHA-256, Zstd-19(CRC-removed bytes)]` against the **smallest** of direct Zstd-19, XZ-9 and Brotli quality 11 on exactly the original bytes. Charge **every** candidate header byte; do not gift external geometry/CRC bytes. Independently reconstruct all original bytes and require equal SHA-256 and byte equality. Report (a) byte gain/loss per input and aggregate, (b) effective CRC opportunity upper bound `(4 * PNG chunks or 8 GZIP footer bytes) / source bytes` before header, (c) encode and read/reconstruction wall, CPU when practical, memory/temporary-work limitations, and (d) refusal/invalid/tamper cases.

Scientific threshold: advance this **format-scoped** seed toward bounded product-admission evaluation only if **each** unrelated format family contains at least two different real positive files with >=5% full-candidate byte savings against its per-file strongest conventional control AND each format's aggregate complete candidate bytes are at least 1% smaller than that control. Otherwise: **NARROW / PARK A14 container-checksum specialization**; preserve any isolated positives but no product grammar or marketing claim. This criterion is deliberately stringent: a gifted format oracle cannot claim generality from one lucky file. A zero/negative result is legitimate, not a CI failure. Independently report an *optimistic uncharged no-header* bound to separate checksum entropy opportunity from packaging debt, but it earns no product credit.

Source root/OS and package distribution are uncontrollable; if sample selection yields <16 valid files in either family or decompression/codec tooling is missing, status is `INSUFFICIENT_CORPUS`, not a negative generality finding. Stronger adversarial tests include modified PNG CRC, truncated PNG, modified gzip footer, concatenated gzip, tampered candidate digest/compressed data, malformed chunk lengths; all must reject, and original input bytes must be unchanged.

## Execution, scope, decision, costs

Cheapest decisive rung: exact format-aware bound + real-data charged oracle, **not CMPCT integration**. No changes to `src/`, `native/`, parser/API, release law, frozen benchmarks, evaluator, Discovery Engine state or #670. Linux local execution is valid **O1b research only**, not cross-host/product proof. Exclude oversized gzip expansions above 8 MiB and report exclusions. Document explicit evidence SHA, strong direct controls, decodability, false-admission boundary, and expected portability/dependency carrying cost. Investigate the offset/permission/hash limits in a separate future decision if result positive.

**Counterfactual test:** If the pre-observable bound `CRC bytes <= 8/file` or `4*chunk_count` is immaterial versus file size + charged metadata, the rest of the family could have been killed without full compression. The instrument must report whether this early discriminator would have prospectively held across all selected inputs; do not retroactively change the threshold.

No release/merge regardless of scientific result; child PR is draft and parent retains ownership.

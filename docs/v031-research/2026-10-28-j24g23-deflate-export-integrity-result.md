# J24G23 result — released direct-Deflate ZIP export lacks physical CRC admission

Date: 2026-10-28 UTC
Status: DECISIVE RELEASED-SOURCE NEGATIVE; PRODUCT FIX NOT LANDED
Preregistration: `2026-10-28-j24g23-deflate-export-integrity-prereg.md`
Released control source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`
Research PR: https://github.com/FCMO-AI/.CMPCT/pull/706
Exact measured research HEAD: `4cf029d74b0452cf1f5ad5afeba15fba694cca60`
Hosted run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40772032980 (SUCCESS)
Original artifact: ID `12853730450`, SHA-256 `74fa74c6691d5469da9ff7fd3a79cacbc9ee6f2ab24746ee209db67782c5fa9a`

## Primary question / result

**CONFIRMED** under the actual installed published Builder, Writer and Reader. An authentic CMPCT physical revision-24 archive built through Builder's nested-ZIP Deflate reuse and subsequently reduced through public `append_delete` retains one directly Deflate-backed regular file (`S_BLOB`, `CODEC_DEFLATE`). The ordinary Reader `read` and `verify` reject a one-bit mutation to the physical blob header CRC32; `export_zip` nevertheless returns success and publishes a ZIP whose local and central CRC32 values are the corrupted value.

The resulting ZIP is invalid to an independent standard-library ZIP consumer. The existing direct-Deflate optimization transfers physical header metadata and Deflate bytes without physical validation.

This is not a claim of cryptographic signature forgery or an actual-world data-loss incident; it is a **demonstrated physical-corruption acceptance divergence** between released public APIs.

## Physical original and altered control

- Valid source CMPCT SHA-256: `c2111c808d1e4f7365d5db3bb1ce5a1451cb097df178129237691552f45bb8a8`
- Altered source CMPCT SHA-256: `1ef43ead63912c1529dc629535ba17473ec3cb525bc9e8836e8c42f7dd0ffd27`
- Exactly one source byte changed, one bit at physical offset **536**, inside the Deflate record's CRC field; no index/footer/payload bytes changed.
- Physical Deflate stream: **131,112 B**, decoded member: **131,072 B**.
- Actual decoded content SHA-256: `1af6da656624174e4940374fc9779b5a551c25b813c94c7dea2a3d83fc8168a5`.
- Valid stored CRC32 `2336205842`; mutated `2336205843`.

| Operation | Baseline | CRC-mutated physical source |
| --- | --- | --- |
| `CMPCT.read` | ACCEPT | REJECT: `OSError: blob integrity failure` |
| `CMPCT.verify` | ACCEPT | REJECT: `OSError: blob integrity failure` |
| `CMPCT.export_zip` | ACCEPT | **ACCEPT: incorrect** |
| `zipfile.ZipFile.read` of export | ACCEPT, exact original bytes | REJECT: `BadZipFile: Bad CRC-32` |

- Valid ZIP SHA-256: `8445ad472bb5130e05b41bb1e1030930003a9d61d56a6a91db67605fab6afead`
- Altered ZIP SHA-256: `3315bcfbf1078ede7e61a70fbbf28986801475132b85e78741ca3e53b1bc59f8`
- ZIPs differ at exactly **two bytes**, one in the local CRC (offset 14) and one in central-directory CRC (offset 131171). Compressed Deflate bytes remain identical.

## Independent raw-wire referee

An independent Python-stdlib-only auditor downloaded the original hosted ZIP and inspected physical `BHDR`, raw Deflate payload, CRC32, SHA-256, ZIP LFH, central-directory CRC and emitted ZIP compressed stream **without importing CMPCT or the source test instrument**. Its 35 checks passed. The audit independently decompressed the Deflate payload and proved that both exported ZIPs copy the identical physical stream, while the corrupted export has the wrong CRC twice. Source and output hashes matched the original hosted receipt.

Original artifact SHA-256 `74fa74c6691d5469da9ff7fd3a79cacbc9ee6f2ab24746ee209db67782c5fa9a`. This is an independent physical-framing audit, not a second general-purpose CMPCT reader.

## Mechanism / counterfactual

The direct-Deflate zero-recompression optimization crosses a **format-integrity boundary**: it publishes archive-controlled compressed data plus an unverified physical header into a new container, while ordinary reads validate actual decompressed CRC and length. The cheapest prospective falsifier was to flip just the physical frame CRC (preserving actual stream), proving whether re-encoding had been replaced by unchecked trust in physical metadata.

Had this check preceded performance optimization, it would have exposed the missing proof boundary without needing a complete adversarial corpus or release benchmark. That is a transferable code-review/experiment-selection lesson, not enough repeated evidence to change Discovery Engine policy.

## Strongest caveats and product gate

- One tested corruption class, one Ubuntu/Python 3.11 host, real Builder/Writer pipeline, no exhaustive fuzzing or full parity benchmark.
- Output ZIP size was identical; only CRC fields changed. No performance win was claimed from raw one-off wall timings.
- Repair must verify physical Deflate data (at least ordinary Reader's decompressed size/CRC) **before** exporting its original exact compressed bytes; a portable implementation must survive malformed headers/truncation, repeated owners, fallback path and cross-platform CI.
- Reusing decoded-cache entries while rereading mutable mmap compressed bytes is not proof of identical-version custody. Validate a self-consistent compressed-byte snapshot or explicitly prove source immutability.
- Source `main` unchanged, on-disk revision 24 unchanged. This research contains no product fix, merge or release credit.

## Concurrent ownership and next executable action

Narrow direct-Deflate export issue was unclaimed in the inspected open-PR/issue titles at activation start. PR #703 owns the distinct stdout/cat pipeline and remains untouched. Next: a separate candidate branch, source-exact failing historical control, smallest snapshot-validated physical Deflate check in `_direct_deflate_stream`, positive ZIP exact-stream preservation, hostile variants and entire product gate. Do not mislabel research SUCCESS as product compatibility or release SUCCESS.

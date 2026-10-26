# O156 result — ZIP export portable logical-name fidelity (2026-10-26 UTC)

**Classification:** decisive negative product/interoperability evidence on the authentic r24 Python Reader; no correction, no release credit.
**Original preregistration:** commit `cb7c4d81f92dda2e3b35dcb3a5e5af85bedb0a55`, before instrument.
**Source baseline:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
**Measured instrument HEAD:** `bf3c857544ce6236f29e95ce9a24a6f3b4a71ff9`. No CMPCT product files were modified.

## Exact-hosted evidence

GitHub Actions [40278444729](https://github.com/FCMO-AI/.CMPCT/actions/runs/40278444729) ran the installed branch Reader plus Python's independent `zipfile` decoder/extractor on **Ubuntu 24.04 and macOS 14**; both jobs **SUCCESS**. Per-host evidence retained in:
- Ubuntu original logs/job `121426170005`; archive [12630189929](https://github.com/FCMO-AI/.CMPCT/actions/runs/40278444729/artifacts/12630189929).
- macOS original logs/job `121426170230`; archive [12631655173](https://github.com/FCMO-AI/.CMPCT/actions/runs/40278444729/artifacts/12631655173).

The checkout asserts exact `EVIDENCE_HEAD`, authentic Git ancestry of preregistration, Reader/path-policy/source blobs, and the independently authored immutable `tests/conformance/v24-direct-codecs.json`. Each physical blob span remained byte-for-byte identical to its original golden. Both stored indexes were reconstructed with valid Zstd and SHA-256; neither checksum was bypassed.

## Observation

For each of RAW, Zstd and Deflate, three same-input cases were executed on each host:

| Authenticated logical stored name | Direct `CMPCT.extractall` | ZIP `zipfile.extractall` on POSIX | Agreement |
|---|---|---|---|
| Original golden (e.g. `raw.bin`) | `raw.bin` | `raw.bin` | YES |
| `nested/leaf.bin` | `nested/leaf.bin` | `nested/leaf.bin` | YES |
| `nested\\leaf.bin` | `nested/leaf.bin` | literal `nested\\leaf.bin` pathname | **NO** |

**18/18** cases reconstructed byte-identical logical contents; independently computed SHA-256 and ZIP CRC validation passed. **12/12** simpler/original controls preserved relative path identity; **6/6** backslash variants produced the predicted different output pathname. All three codecs showed the same result on both hosts. The original bytes and physical span remained intact.

This is **not a content corruption claim**. It is a portable namespace-fidelity mismatch: `canonical_logical_path` interprets backslashes as separators for CMPCT extraction, but `export_zip` writes the raw stored name as a ZIP entry without normalization. On POSIX, conventional Python ZIP extraction creates a backslash-named file rather than the nested path. A consumer can therefore reconstruct different filesystem namespace semantics from the same authenticated CMPCT logical tree by choosing the direct or ZIP export route.

## Negative scope and self-critique

- The experiment does **not** show behavior on Windows, all ZIP tools, archive-entry name collisions, hardlink/symlink graphs, Unicode casing, ACL/xattrs or giant ZIP64 paths.
- A one-file vector does not prove there are no interactions across multiple entries; future integration must test mixed slash/backslash path aliases and ensure the existing canonical duplicate guard remains fail-closed.
- These paths were created by valid re-authentication of independent goldens rather than by a normal Builder run. That is intentional: the Reader contract must handle any admitted valid r24 index; a normal Builder need not emit the adversarial spelling.
- No performance, physical RSS, compressed-size or release evidence was obtained. Future formatting decisions could intentionally preserve raw names, but that would make the cross-format namespace mismatch an explicitly documented compatibility limitation rather than eliminate it.

## Causal decision / concurrency / future step

The smallest decisive discriminator was an authenticated filename-only transformation plus an independent extracted-tree name comparison. Merely checking ZIP member bytes or SHA-256 would have missed the discrepancy. There is no evidence-backed reason to change the Discovery Engine policy on one result.

No colliding implementation was opened. O149/O150 own staged ZIP publication, O151/O153 own physical-output parity and economics; this O156 PR is science-only. **Owner next action:** decide whether ZIP output should use the canonical slash-delimited logical key (and prove collision-safe output of all rows, including directory/symlink cases) or whether raw spellings are an explicit limitation. Run the new golden-derived negative alongside retained ZIP export failure-atomicity and official tests before any promotion. Do not merge or release on this result alone.

## Exact-head CI classification

O156 scientific court: **2/2 SUCCESS** at instrument HEAD `bf3c857544ce6236f29e95ce9a24a6f3b4a71ff9`. General Tests and release/benchmark gates are separate; no claim of green general tests or release readiness. Product implementation changed: **none**. Format changed: **none**.

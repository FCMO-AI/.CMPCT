# J24G32 — authentic committed-journal → legacy ZIP cross-boundary falsifier (preregistration)

Status: **FROZEN PREDICTION BEFORE INSTRUMENT AND RESULT-BEARING RUN**. Research / product conformance evidence only. No Reader/Builder/Writer/format/release edits.

## Authority and provenance (2026-10-29 UTC)
- Released v0.30.0/r24 source `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Exact inherited staged ZIP composition #727: `d1e37c2ce319b9c08bacffa8c6148b95eebb7af9`, Reader blob `cd6a2971396d6fe02a1d7f460d850107b3dcc397`.
- Writer transactions source at this head: `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`; no application edits authorized here.
- J24G30/J24G31 covers ZIP calendar, staged publication, and small Builder→ZIP tests, but **not** a genuine committed update/rename/delete journal preceding ZIP interop.
- Existing journal owner PRs (#243/#245/#250, #345) own their respective safety and semantic fixes. This run must not change their code. No discovery state mutation (#574 owner).
- This is a **different cross-layer semantic conformance question**, not another date/Deflate tweak; prior repeated ZIP-family activations force a mechanism frame review, hence test end-to-end journal ownership with both historical Reader and composed Reader rather than reopen calendar.

## Primary question and prediction
Can a genuine v0.30 Builder archive, after a series of committed append operations (rename an existing regular file to a Unicode leaf, delete a second member, update a third member), be exported to interoperable legacy ZIP from the *latest effective generation* with exactly the live names and logical bytes, and without reviving a deleted/renamed name? Also, is a non-footer orphan tail ignored identically by Reader and ZIP export? 

Predict: released and composed ZIPs on the **same physical archive, same host, same ZIP method/settings** must be byte-identical for ordinary in-range timestamps; both must expose the same two live files, exact SHA-256/CRC, name set and UTF-8 ZIP flags. The orphan-tail copy should either recover consistently with fully verified data or expose a real cross-boundary recovery failure. Do not hide unexpected failure.

## Materially different alternatives / controls
- Source-only assertion that export loops `self.files`: cheaper, but cannot verify actual post-journal indices and legacy ZIP acceptability.
- Patch product ZIP writer: rejected absent a proven failing example and conflicts with #492/#727 owners.
- Selected: one exact released Builder/Writer source generates each physical archive; two **separately installed** Readers from released vs composed heads export that **same** archive; a third stdlib-only auditor inspects ZIP names/contents/hash/CRC and compares output bytes. External Info-ZIP `unzip -t` where host supplies it.
- Fresh child processes prevent Reader module cache/source blending.

## Kill and scope
Fail or narrow if any Reader rejects its own committed archive; stale/deleted names appear, Unicode names corrupt, file content differs, output ZIP is rejected by an independent ZIP decoder, archive source bytes mutate, or source fingerprint differs. Never reclassify these as a green test. Archive-level hardlinks, directories, 4GiB ZIP64, temp-I/O, peak RSS, crashes and malicious filesystem swaps are **outside** this limited conformance court, and a PASS earns no release or performance credit. The orphan tail is deliberately **not** authenticated as a new generation.

Keep raw manifest and both output ZIPs and produce a result JSON with source SHA, ZIP SHA, platform, count, fields and failures. Dedicated three-host CI is a scientific falsifier, not a substitute for General Tests or release parity. Data are public synthetic generic bytes; no personal or private content.

# O197 — Independent Info-ZIP conformance for authentic 4 GiB CMPCT ZIP64 (PREREGISTRATION)

Date: 2026-10-26 UTC. Status: prospective, **frozen before this activation's implementation or hosted evidence**.
Exact inherited scientific source: O196 PR #526 HEAD `38c73861917420184c00e99186d6c747b3a8258d`, itself on O193 #521; published CMPCT stays v0.30.0/r24. Product owners O193 and O196 remain unchanged. No format, Reader/Builder, historical comparator or release change.

## Primary single scientific question
Can independently maintained Info-ZIP `unzip`, **not CPython zipfile**, consume the **exact genuine 4 GiB ZIP64 member exported by the installed O193 CMPCT Reader from a genuine Builder-authored S_SPARSE revision-24 archive**, confirm CRC through its own parser, stream all 4,294,967,296 decoded bytes and produce the independently recorded source SHA-256?

## Baseline and alternative explanations
O196 on source-authenticated PR #526 established one Linux-built 4 GiB S_SPARSE archive, byte-identical ZIP output on Ubuntu/macOS/Win, full readback SHA/CRC through CPython's zipfile, and independently parsed ZIP64 local-header fields. Its SHA/CRC reader shares a Python library with its writer, so an independent mature consumer is still needed. Earlier #275 established Info-ZIP's ability to read **synthetic** ZIP64 offset/count fixtures, *not* CMPCT-produced full 4 GiB content.
An external failure may be due to Info-ZIP version/tool availability, ZIP64 grammar divergence, unsupported large streaming, CRC/data corruption, or host limits—not automatically a CMPCT compression defect. Preserve stdout/stderr, version, hashes and precise failure boundary.

## Actions PARETOBONKed
- Re-run O196 Python zipfile full hash: already proven; low information.
- Change O193 exporter to custom ZIP64 writer: premature and duplicates ownership.
- Use Info-ZIP 6.x on Ubuntu to read the actual CMPCT product output: cheapest mature independent grammar and full-content falsifier; **selected**.
- Broader three-host external matrix: more cost but source ZIP bytes were identical on three O196 hosts; defer until one independent consumer establishes value.

## Prediction and controls
Positive prediction: `unzip -tqq` returns 0 after processing the real ZIP64 member; `unzip -p <zip> sparse.bin` returns 0 and emits exactly 2^32 bytes; a bounded 4MiB stdout drain calculates exactly the original source SHA; ZIP size, raw SHA, and O196 receipt agree before and after. ZIP64 64-bit field size must be 4,294,967,296 with valid 32-bit sentinels (already independently checked in O196, and reconfirmed).
Host-positive control: capture `unzip -v` and a small known-good ZIP before the giant comparison. Negative control: make a *separate copy* of ZIP, flip a deterministic compressed-data byte without rewriting central CRC/index; `unzip -tqq` must fail on corruption. The positive ZIP and CMPCT source must remain byte-identical after either test.
If the external command is missing, route is infrastructure BLOCKED not scientific FAIL; never claim independent conformance. If positive fails while the tool supports the known-good control, narrow the claim, retain logs, and notify O193 owner.

## Kill/narrow/promotion rules
- Any authentic external read returning a wrong length/hash, nonzero exit, or failing CRC **falsifies** O197's scoped external-consumer claim; do not reduce size or silently ignore errors.
- A tool exception or unsupported ZIP64 must remain ambiguous until an independent known-valid large control separates tool limitation from CMPCT product.
- Negative control acceptance is essential to substantiate the actual independent verifier.
- Even a complete PASS proves **one sparse 4 GiB profile on one external reader**, not arbitrary ZIP64, security, crash recovery, resource bounds, 15/15 domination, or release readiness.
- Do not edit O196's original receipt or code to make this green. Real run identity, source HEAD, instrument SHA, and raw JSON must persist.

## Expected decision unlocked
If PASS: external parser/consumer interoperability debt on one genuine large-member profile is closed; next priority pivots to adversarial member structure/resource caps or publication integrity. If FAIL: give the single O193 owner a narrow external incompatibility reproducer rather than adding another writer. Never silently broaden `docs/discovery/STATE.json`; this PR itself is durable science.

## Experiment scale and cost
One Ubuntu 24.04 hosted runner, one authentic CMPCT Builder source (4 GiB logical / ~16 MiB physical allocated), one installed source-authenticated O193 Reader ZIP64 export (~4.4 MiB output), an Info-ZIP CRC test and 4 GiB stdout streaming hash, plus a corrupted-copy negative. Keep output piped, not materialized as a 4 GiB filesystem file. Record complete stored bytes, build/export/read wall when available, Info-ZIP version, decoded bytes, SHA, archive and ZIP hashes, process exit codes, and limits. No cross-OS timing comparisons.

## Concurrency and integrity
Current O196 owner #526 and O193 owner #521 are independent; this branch only adds O197 experiment files. `docs/discovery/CONCURRENCY_PROTOCOL.md` was not present on the inherited source. Re-check owner PRs and branch before late edits, never overwrite their files. No mutation of shared discovery state, canonical branch, frozen benchmark or version.

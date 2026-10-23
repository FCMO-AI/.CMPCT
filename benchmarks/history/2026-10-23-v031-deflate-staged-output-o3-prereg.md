# CMPCT v0.31 — O3 staged-output verification before publication (preregistration)

Date: 2026-10-23
Status: **PREDICTION FROZEN BEFORE O3 CODE OR RESULT**.
Experiment ID: `v031-deflate-mutable-source-staged-output-o3`.
Base of O3: research branch `agent/phased3-v031-deflate-export-mutable-source-o2-20261023` after O2 result `cf5633c7394243d9357ee0e40b23574652c62315`. Parent product owner remains PR #284 Reader source blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`; **no product source edits allowed**.

## New question

O2 showed that PR #284's preflight correctly rejects static corruption but cannot prevent a post-preflight concurrent writer from mutating source bytes before ZIP stream reuse. Does a **verified staged OUTPUT** provide an effective, low-risk containment alternative, even if the source is mutable between verifier and copy?

## Proposed mechanism and prediction

Wrap the **unmodified** `CMPCT.export_zip()` in a separate research-only function that writes a unique private same-directory temporary ZIP rather than the named destination. Freeze expected logical SHA-256, CRC32 and lengths from the source's original physical Deflate headers before invoking export. After export, independently parse the **staged ZIP bytes**, stream-read every actual output member in <=64KiB chunks, compare SHA/CRC/length to the original commitments, and only then atomically `os.replace` the staged ZIP to its target. On any failure unlink the staging file and leave an existing target untouched.

Predictions:
1. Immutable clean archive: exported bytes equal ordinary export exactly, fully verified and published.
2. Static physical corruption: inherited export guard rejects, private staging cleaned, destination preserved.
3. Deterministic O2 mutation after successful original preflight: the original exporter writes bad staged bytes, but postcopy stage verification fails, leaves destination unchanged and no temp files.
4. Same mutation with three aliases: all logical members must be checked or publication rejected on first violating alias. No corrupted output is published.

**Disproof:** any unverified destination replacement; any successful publication of post-preflight corrupted member; any change to valid ZIP bytes or loss of byte-exact reused Deflate physical stream; any leaked staged output after reject.

## Stronger simpler controls and costs

- Revalidate live source before output copy: insufficient, same TOCTOU window.
- File stat/mtime comparison: not a cryptographic snapshot or race-resistant invariant.
- Materialize whole source stream in memory: simpler, but compressed-member-sized RSS and duplicate alias copying; not an acceptable general solution.
- Stage output then verify actual emitted bytes: bounded 64KiB read chunks, output-sized same-filesystem disk space and a full additional read/decode/hash pass. This is intentionally a correctness-first oracle; it may lose speed.

Do not misattribute an external `zipfile` CRC-only check as proof of CMPCT SHA: compare a separately preserved original logical SHA-256. The authority of those header commitments is assumed for this payload-only mutation model; an adversary able to alter archive metadata/index, the staging directory, the target inode, or the process has a different threat boundary.

## Evidence rung / limitations

Source-exact installed-package research harness on Ubuntu/Python 3.11. No production Reader/Builder or release modifications. No user filesystem writes, private data, secrets, benchmark claims, portability guarantees or durability guarantees. `os.replace` is atomic namespace publication on same filesystem, but not crash persistence without fsync; do not assert crash durability. High-ratio large archives and ZIP64 >4GiB remain unmeasured.

If positive, owner decision is a bounded stage-and-authenticate implementation or a credible enforceable immutable-source contract. Product promotion still requires portable temp ownership, cross-platform safety, memory/CPU/IO, duplicate physical blob economics, hostile payload/index checks, complete official gates and recovery.

This is a different architecture proof than O2; no global discovery policy change is authorized.

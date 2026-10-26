# O143 — ZIP export failure-atomicity: preregistered falsifier

**Date:** 2026-10-26 UTC. **Category:** science / safety, no product source modification.

## Current authority and ownership

- Canonical v0.31 development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Independent parent owner: O140 PR #488, exact commit `d8b69758dbcbb66fe28fa7cf59598916df160d2d`, Reader Git blob `e46e6121842d485cb209118576ebf3ba3719080d`; PR #488 owns special ZIP-export output types on top of O135 #483 and O284 direct Deflate integrity.
- Existing ZIP-export product owner PR #284 explicitly lists **non-direct member failure leaving partial ZIP output** as separate unclosed lifecycle debt. This experiment **does not duplicate** #284's direct-Deflate-stream validation, #483's own-source alias protection, or #488's nonregular-output admission.
- Frozen Builder-independent r24 RAW member: `tests/conformance/v24-direct-codecs.json`, Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`.

## One primary question

Does exact-head `CMPCT.export_zip()` leave an existing **ordinary regular-file ZIP destination** unchanged when export of a damaged, non-direct-Deflate CMPCT member fails? Also: does it leave a **partial ZIP output** when a later member fails after a valid earlier member is serialized?

## Prediction (before the test or measurements)

1. Control: pristine independent r24 RAW oracle exports to a valid ordinary ZIP and reconstructs the frozen logical SHA exactly.
2. Freeze ordinary target containing a valid unrelated ZIP, then alter **only one physical RAW blob CRC32 field** in the independent r24 archive. Ordinary `CMPCT.read()` rejects it; `CMPCT.export_zip(existing_zip)` raises **after** opening/truncating the target. Target SHA and valid ZIP contents change; no original archive alias is involved.
3. Construct a two-member deterministic archive using the current Builder as a *separate genuine installed-product court* (not a frozen format conformance vector), with a small sorted `a_good.bin` and `z_bad.bin` using distinct direct RAW/Zstd blobs. Alter only the physical payload of the later member, leaving index/footer structurally intact. Precheck that ordinary `CMPCT.read(a_good.bin)` passes and `CMPCT.read(z_bad.bin)` fails. ZIP export raises after writing the first local ZIP entry, leaving the original destination overwritten by a nonempty **incomplete ZIP**.
4. Repeat on Linux and macOS (Windows optional) and preserve raw observations, checksum boundaries, source Reader/blob/git HEAD, failures and artifact identity. Distinguish independent fixed-wire evidence from Builder-derived integration evidence.

## Strong simple control, alternatives, disproof

- Stronger control: stage ZIP output to sibling temporary regular file, validate complete archive, then atomic replace after success. Not implemented here: this changes inode/hardlink publication semantics and temp-I/O/storage; must be tested against owner contracts. An alternative fail-closed *preverification of every logical member before output open* avoids some corruption but duplicates decode and cannot guarantee failure atomicity for write errors during publication.
- **Disproof:** parent exporter already preserves existing ordinary output on both corrupt cases; original input mutation is not detected by Reader; second member is not actually direct RAW/Zstd or not reached after a successful first local entry; ZIP remains an independently valid complete archive after failure; or evidence/installation source does not bind exact intended Reader.
- Any instrumentation/fixture failure is classified separately from product behavior and may not be relabeled as a pass.
- Successful reproduction earns scientific **negative** evidence and owner handoff, not product/security promotion. No gates, comparators, version, format, release metadata, or Discovery Engine state may be altered.

## Limits and verification

No attacker-authenticated re-signing, concurrent namespace pivots, crash/power-loss atomicity, ZIP64 limit, filesystem durability or Windows device semantics is claimed. Individual filesystem write errors are a separate possible midwrite failure. Runtime outcomes must be captured by a source-bound GitHub Actions court on exact HEAD, with no shortcuts to the immutable evidence boundary.

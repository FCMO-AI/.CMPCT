# O80 — Prospective three-family Builder source-fidelity composition

Date: 2026-10-25 UTC. Status: **PREREGISTERED BEFORE INTEGRATION AND BEFORE RESULT**. Scientific/product scope: unreleased CMPCT v0.31 revision-24 Builder. Released v0.30.0 and format unchanged.

## Authority / ownership and collision check

Base **O64** PR #419 exact HEAD `9de342226bfbce3690ef1c8cabb1fdf229dbf003` (Builder blob `b02a30d4ad1b26ea8eea49e11159113caebd6006`). It already contains O47/O48/O50 Windows regular-hardlink identity, unsupported-special-file rejection, O57 Win32 regular-file ADS detection, and O64 root/nested NTFS directory-ADS admission. Two independent owners to compose, not silently overwrite: **O65** PR #420 exact HEAD `314c5bcc4d555e894cf5024918da3b5358e726b8` Builder blob `7f222458adc1c4aae65fa24650a8fc0c7b0c1b18` adds fail-closed xattr read/enumeration error handling; **O67** PR #421 exact HEAD `30a572640de6a7612e09fb579860e228cb2679d8` Builder blob `636cacef95c518b5ad67c101a5430de5b68d45c6` adds selected-tree physical hardlinked-symlink refusal. Both O65 and O67 were studied individually. O65 began on original development and therefore its full Builder must **not** be transplanted: this would remove O47/O48/O57/O64. Only its precise metadata error-handling delta is eligible. O67 is stacked on O50; only its symlink-inode guard is eligible. No other current open PR claims this exact O64+O65+O67 composition; recheck before late shared writes.

## Prospective question and predicted outcome

Can the three independent guarantees coexist in one actual installed Builder, without regressing inherited hardlinks, NTFS stream admission, supported symlinks, xattrs, determinism, reader reconstruction or no-clobber safety? Prediction: all unchanged O47/O48/O50/O57/O61-D2/O64/O65/O67 tests pass with their **real executed** platform-specific exclusions; a new cross-feature POSIX source test rejects only selected-root symlink aliases while preserving existing archive, and after alias removal it stores and restores source xattrs with unchanged hardlink topology. Windows ordinary+ADS controls remain accepted/rejected as before. No data/format/reader/codec modifications.

## Alternatives and strongest controls

Controls: untouched owner tests, original O64 source and exact existing O65/O67 test blobs; preserve both source-identical owner tests without weakening assertion or skip criteria. Alternatives: accept separate PR green as proof of composition (invalid); transplant entire O65 Builder (deletes O47/O48/NTFS guards); relax any historical source-locked baseline check (forbidden); add universal new source snapshot or new wire representation (higher carrying cost and differently-owned unresolved threat). Choose smallest diff and installed-wheel three-platform court.

## Falsifiers / promotion boundary

Kill/narrow on: any inherited supported-tree byte or tree mismatch; silent xattr error; unsupported ADS admitted; hardlinked symlink alias silently published; external-only selected symlink falsely refused; ordinary equal-target independent symlinks conflated; Windows hardlinks lost; unexpected path overwrite; actual test errors or skipped mandatory test cases; missing JUnit/custody receipt; product performance byte or time regression beyond current normative gate. This preregistration authorizes a **draft candidate only**, not merge or release. Exact-head CI evidence may be pending and cannot be claimed as passing.

## Economics and limitations

O65 adds no successful xattr syscalls; O67 uses already obtained lstat and an O(n_selected_hardlinked_symlinks) dictionary; O64 already pays Win32 directory/regular ADS enumeration. Actual complete Builder CPU/wall/RSS on new composed candidate, live filesystem races (O52), atomic snapshot, true Win32 symlink-inode alias semantics, and official ABBA are **unmeasured**. Keep their debts explicit. All evidence is synthetic/public with no user or private corpus data.

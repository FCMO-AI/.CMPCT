# J24I16 — Win32 intermediate-junction custody falsifier (preregistration)

**Status:** preregistered *before* new instrument/workflow; research-only, no product or release modification. Date: 2026-10-29 UTC.

## Authority and coordination
- Canonical `main@80c358f8824ec1b20d349c92ed94c898090969b0` publishes CMPCT v0.30.0/r24. This branch starts from J24I15b #736 exact research HEAD `8d4343defe2918257e153654f1e59cdb7253f265`; its installed Windows micro result (23.32% lower micro wall versus O47) is a **leaf-only** seed, not a Builder claim.
- Builder post-stat/parent pivot research is owned by #407/#408; Linux rooted source alternatives are #434. Hardlink Builder ownership is #401, compaction integration #730. This separate question measures **Win32 intermediate-component semantics**, which those hosted courts have *not* established on Windows. Do not change their implementations or claims.
- This study does not assert the published Builder admits a junction, nor that a user can remotely exploit it. A failing scoped primitive may rule out an unsafe product architecture.

## Primary question
Given a selected source root, does `CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS)` plus the existing J24I15b cached handle reader prevent traversal of **ancestor directory junctions**? Its protection of a *final* symbolic-link leaf is already established.

## Prospective predictions and decisive controls
H_leaf_only: a legitimate regular leaf is admitted; a final symlink to an outside regular file is rejected; but replacing an admitted parent directory path with an NTFS junction to a different, external directory makes the same leaf-only Win32 API read **outside bytes** and report the outside file's physical identity. No timestamp race or randomness required. An unchanged stable path remains inside. The pre-pivot `os.stat` source identity and post-pivot handle identity should differ (unless host filesystem deliberately aliases them, which is separately reported).
H_full_path: the candidate rejects the intermediate junction, or returns the original inside bytes, preserving root confinement. This falsifies H_leaf_only for this host/runtime.

Controls: preserve distinct SHA-256 sentinel contents inside and outside; verify `os.lstat` identifies the intermediate junction as a reparse point; verify `Path.resolve` and the outside pathname identify the same outside file; verify the final-leaf symlink is independently rejected; before replacing a parent path record the exact inside source path/file hash; perform a deterministic parent rename+junction rebind before the HANDLE open. The test must fail if no junction or symlink can be created; environment privilege failure is INFRASTRUCTURE, not product correctness.

## Evidence and kill boundaries
- A **positive outside-read** is a bounded security *architecture falsification* of final-leaf-only source confinement. It earns **no** product regression, release readiness, exploitability, or quantitative performance claim. Never promote a final-only nofollow adapter as source-root safe.
- If outside read does not occur, record exact Windows error, source/root identity, link nature and endpoint, and whether it reflects a real safe contract or missing test capability.
- Full Builder admission, root-relative HANDLE traversal, parent reparse detection, ancestor pivot interleavings during enumeration, deferred ZIP/sparse/xattr paths and full create/RSS/CPU remain future productization obligations.
- Independent evidence: exact Git HEAD and inherited instrument blob, physical content SHA, physical file IDs, mutable path before/after, direct/final/ancestor cases, host identity, raw receipt and reproducible JSON. Retain failures and negative evidence. Do not change evaluator/safety thresholds, format/release files or v0.30 artifacts.

## PARETOBONK
Cheapest decisive action is a one-host Win32 primitive experiment using the already measured cached nofollow leaf helper. Another complete Builder implementation or broad benchmark would duplicate ownership and obscure the security boundary. Alternative stronger control is *per-component* rooted HANDLE traversal or equivalent reparse-aware tree custody; its cost/portability is not yet measured.

**Prospective decision:** `ANCESTOR_JUNCTION_TRAVERSAL_CONFIRMED` means final-only nofollow is demonstrably insufficient for root confinement. `NOT_REPRODUCED` means no such claim; inspect the true observed reason. `INFRASTRUCTURE_BLOCKED` is not a security pass.

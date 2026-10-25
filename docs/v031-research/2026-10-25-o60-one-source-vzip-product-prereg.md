# O60 — One-captured-source VZIP productization preregistration

Date: 2026-10-25 UTC
Status: **PREREGISTERED / NOT YET MEASURED**. Immutable baseline: O50 PR #405 `17c96603e33b02b3f2f9e0079eec2b128f293be8`; shipped product remains v0.30.0 / r24. This branch is an independent productization of the distinct O55 test-only oracle (PR #410); O50 remains owner of its Builder O47/O48 composition. No merge/version/release authority.

## Primary falsifiable question
Can the real r24 Builder make every deferred ZIP/WHL recipe, storage fallback, whole-file identity and size from exactly **one captured byte sequence** while retaining complete stable-input archive identity and existing validation, including an in-place same-inode source mutation after capture?

Historical flaw: O54 PR #410 demonstrated original O50 may emit an unreadable archive by combining independent path reads. O55's detached in-memory recipe oracle passed on three hosts for STORED, DEFLATED, MIXED and same-size post-capture mutation. Neither changes product.

## Baseline/control/mechanism
The original `codec.make_vzip_recipe(path, add_content)` calls `path.read_bytes()`, `ZipFile(path)` and `open(path)`; `Builder.scan()` reads the deferred path again for fallback and logical SHA. The simpler competing control of pre/post-stat is insufficient against same-inode equal-size mutations. Filename lock or pathname-inode equivalence is not an immutable byte snapshot. Instead, one Builder read supplies `original` to ZIP metadata, member decoding and compressed span extraction through in-memory I/O; the same `original` supplies fallback bytes, file length and SHA. Preserve existing public codec call compatibility and r24 encoding; do not change ZIP member assumptions, encoding policy, Reader or thresholds.

## Predicted acceptance
1. On each of Ubuntu, macOS and Windows, real Builder+Reader installed from this exact branch must round-trip three stable 3-member ZIP classes (STORED, DEFLATED, MIXED), and compare complete archive bytes against a **real historical O50 binary/source comparator** over the *same source*; exact equality required.
2. An in-place A-to-B rewrite of equal size after the captured read, preserving source inode and path, must yield a successfully verified/readable r24 file representing A and matching a baseline stable-A construction, not a hybrid. Observe exactly one deferred original-source read.
3. The 8+ container-pack branch must retain real exact byte reconstruction/identity; corrupted or unsupported ZIP cases must preserve explicit fallback/rejection semantics, never silently claim proof from an oracle.
4. A production regression cannot be rescued by altering historical O54/O55 preregistrations, validators or comparator semantics. CPU/wall/RSS, copy/I/O, fallback/virtual admission, all general and full-PR performance gates are debt until genuinely measured on exact promoted source.
5. No product credit solely from detached oracle or skipped matrix. The commit/PR remains draft until all required product and release gates are confirmed.

## Kill or narrow
Any stable whole-archive byte mismatch, unverified physical content under the exact after-capture adversary, loss of established fidelity/safety, or confirmed release-gate byte/performance regression prevents promotion. Source change *during* the initial capture remains outside the proven guarantee and must be documented, not assumed atomic.

## Concurrency
Check current #405, #410, #413/#414 before late writes. Dedicated branch based on O50 exact parent; no changes to owners' branches. Follow-up owner handoff only after source-exact evidence.

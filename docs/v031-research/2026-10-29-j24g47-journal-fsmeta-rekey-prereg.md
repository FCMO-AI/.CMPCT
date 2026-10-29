# J24G47 — Prospective revision-24 journal metadata-identity repair
Date: 2026-10-29
Status: PREREGISTERED BEFORE PRODUCT CODE. No merge/release authorization.
Source owner: #770 exact 78b9dd2d148350898c95a0cdbeefe760de2e567e (research), stacked on #757/#428. Published main remains v0.30.0/r24.
Issue: #771.

## Primary scientific question
Can one path-identity-preserving journal-op primitive used by BOTH incremental Reader replay and 64-generation Writer checkpoint construction preserve the authenticated, sparsely positional `fsmeta.xattrs` and `fsmeta.owner_overrides` fields without changing revision-24 disk bytes, weakening validation or adding per-member update metadata not present on disk?

## Baseline and controls
#770 (J24G46) independently proved physical native Linux/macOS metadata misassociation after append of a lexically earlier member. Stable same-path update is the stronger unaffected control. Baseline mechanism: `Reader._index_from_footer` re-sorts rows after journal ops while treating ordinal-keyed metadata as stable; `transactions.append_update/_index_after_op` independently checkpoint with the same flaw. A fix only in the Reader will fail at depth >=63 when the Writer emits a full checkpoint.

## Candidate mechanism
For each actual change in row identity/order, snapshot the prior file row positions and the two indexed metadata tables, apply the original put/delete/rename semantics, then reconstitute sparse ordinal records according to logical path identity on the newly sorted rows. Rename transfers identity; delete discards its metadata; insertion receives no unrelated old metadata. Same-path put preserves inherited metadata, as the existing format carries no new metadata in that delta. `owner` modal/default is unchanged. Same method is reused for Reader delta replay and Writer checkpoint creation. No copying of content blobs or change to on-disk revision-24 schema.

## Explicit alternatives and failure tests
A) Remap only `xattrs` (incomplete: `owner_overrides` same invariant).
B) Reader-only patch (fails after 64-generation full checkpoint).
C) New journal format with path-bound metadata (breaks compatibility; disproportionate).
D) Rebuild metadata from filesystem while reading (not available).
Choose shared name/identity remapping subject to physical adversarial tests.

## Prediction, kill and strongest review
Predict original real J24G46 fixture changes from JOURNAL_POSITIONAL_XATTR_REBIND_CONFIRMED to POSITIONAL_IDENTITY_PRESERVED on Linux/macOS, with the same independently authenticated archive, unchanged origin bytes, explicit owner/inserted association and compaction. Predict no difference for stable source update. Add separate delete, rename, replace and 64-delta checkpoint tests and explicit sparse override remapping. Falsify if any metadata attaches to a newly inserted member, rename loses identity, a checkpoint reintroduces positional drift, or any existing content/format/benchmark invariant fails. Any failure remains recorded. Windows xattr absence is not a positive fidelity test.

## Evidence ladder
First run source-level pure index permutations and static syntax/bounds; then genuine Builder/Writer/Reader physical r24 (Linux/macOS plus Windows content-only); then independent wire/OS verification; then broader exact-head gates. No numerical benchmark credit from specialized correctness tests. Memory bound O(file rows + sparse entries) per actual name/permutation change; unaltered-order updates should reuse existing arrays. Legacy archives already serialized with incorrect associations cannot be recovered by permutation alone; report this irreducible boundary honestly.

## Concurrency and non-claims
This is a *new repair PR* stacked on the existing #770 **research-only** PR, not a rewrite of #770's negative tests; #757 remains the native xattr owner. Avoid modifying release law, frozen court, discovery state, shared owner heads. Before late mutations re-fetch targets. Do not claim that a green reproduction workflow proves product correctness, nor that all UID/GID changes can be applied as an unprivileged user.

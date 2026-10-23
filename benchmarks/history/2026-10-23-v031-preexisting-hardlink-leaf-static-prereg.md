# v0.31 static destination hardlink-leaf alias — prospective falsifier (2026-10-23)

## Source, ownership, and scope
- Target: **FCMO-AI/.CMPCT** revision-24 Reader, stacked only on static destination symlink-preflight owner PR #269 at exact head `0273c628872dce672936aa0ddd555ed10a900bf7` and Reader blob `43fd462535495b0c3c80c95751a20d9c261b94ed`.
- Distinct surface: a *pre-existing regular file leaf with multiple physical hardlink names*, not symbolic-link traversal. PR #269 inspects `lstat().st_mode` for symlinks/parents but explicitly allows ordinary regular-file reuse, while the normal `S_BLOB` and `S_SPARSE` extraction paths open `O_TRUNC`.
- Issue #265 remains the broader trust boundary; this candidate is **static-only**. It does not claim TOCTOU safety, capability-rooted POSIX extraction, cross-platform semantics, or merge/release. Do not modify PR #269 or neighboring Reader owners; one stacked PR.
- Archive input is an authentic Builder-produced revision-24 archive; only synthetic temporary paths are used. The outside comparison refers to an outsider within the same TemporaryDirectory, not an arbitrary host path.

## Prediction preregistered before source mutation
On POSIX/Linux, the authentic upstream Reader will accept `extractall(safe_symlinks=True)` when `dest/member.bin` is a hardlink to `outside/victim.bin`, even though no symlink exists. Because opening an inode with `O_NOFOLLOW` would not help, the existing `O_TRUNC` path changes outside bytes/size without crossing a pathname symlink.

The cheapest source-exact negative: a small `S_BLOB` owner with outside hardlink alias. The distinct structural perturbation: a genuinely sparse `S_SPARSE` file (when filesystem admission supports it). Both must fail closed *before the first earlier member is materialized*. Controls: (a) existing ordinary single-link leaf is reused, (b) existing hardlink leaf under `S_CDC` or `S_CHUNKS` already uses atomic publication and must not be falsely rejected, (c) `safe_symlinks=False` preserves explicit opt-out legacy behavior, (d) no archive data/format change.

## Alternatives compared
1. **Refuse all nonempty destinations**: maximal false rejections, discards legitimate preexisting ordinary file reuse. Reject.
2. **Follow `O_NOFOLLOW`/a lexical/symlink-only preflight**: does not prevent writing the *same inode* through hardlinks. Reject.
3. **Atomic same-directory new-inode publication for all regular members**: stronger static semantics, but changes inode/metadata identity on overwrite, write/syscall/temporary-space economics and overlaps ongoing chunked/sparse owner implementations. Reserve as a separately costed full capability-root path.
4. **Bounded pre-write `lstat` inspection of direct-truncate leaves**: reject `stat.S_ISREG(st_mode) and st_nlink>1` only for regular archive files whose selected storage takes the in-place truncation path. Select as a minimal interim fail-closed safety candidate; no new output-payload copy.
5. **Full anchored dirfd/no-follow + atomic publication across all materialization/metadata operations**: strongest race-resistant route; independently owned future product architecture; not claimed by this PR.

## Success / disproof and evidence rung
- **Baseline falsifier**: original Reader with new failing focused test demonstrates outsider modification or absence of fail-closed exception. Preserve a negative CI or local adversarial witness.
- **Candidate positive**: exact Reader source SHA and installed-package hosted pytest; outsider *bytes, SHA, inode and size* unchanged, no partial earlier file, ordinary single-link overwrite succeeds, existing safe atomic path remains usable, explicit opt-out unchanged, archive verify passes.
- **Kill/narrow**: if `st_nlink` is not observable or the new guard rejects previously valid atomic-replacement classes (CDC/chunks), reject or narrow. If a static outside hardlink is still modified, reject. Any measured release regression opens debt; do not waive gates.
- **Scope of proof**: static POSIX. `lstat` preflight is raceable; hardlinks can be added/replaced after checking. A complete extraction security guarantee requires descriptor-rooted no-follow traversal and publish semantics, plus platform tests. On-disk bytes, revision, hashes, release policy, comparators and evaluators cannot be changed.
- **Counterfactual discriminator**: prior to any full extraction, the pair `(storage_kind_requires_inplace_truncate, existing_st_nlink>1)` suffices to flag this static alias class cheaply; symlink detection alone misses it.

## Promotion law / handoff
No product or release credit from isolated tests. A green focused court is evidence of narrowing one static safety failure, not general destination safety. Require same-runner r24/ZIP timing/no-byte regressions, general/native/fuzz/hostile/platform gates, then owner/merge authority; the parent PR #269 itself remains in draft and #265 stays open. Preserve source SHA, observations and conflicts in this PR rather than overwriting stale `docs/discovery/STATE.json`.

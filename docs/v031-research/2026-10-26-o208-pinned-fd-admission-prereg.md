# O208 preregistration — authenticated admission and source identity (Linux)

**Status:** preregistered before the scientific court, workflow and any result.
**Date:** 2026-10-26 UTC.
**Parent source:** O193 draft #521 `392112ce859db5a7f85be593c82d1cabc1f5131f`. Released v0.30.0 / revision-24 is unchanged.
**Inherited evidence, not re-earned:** O198/#532 and O202/#539 establish ordinary Python Reader sparse-geometry inconsistency; O205/#542 measures 17.1165 ms incremental strict preflight on one genuine high-extent 4 GiB archive and identifies a generic POSIX pathname reopening race. This O208 question changes the **source identity/ownership frame**, not the validation algorithm or cost study.

## One primary question

When the *actual installed* revision-24 Python Reader and existing `preflight_archive` are executed on **authentic independently Builder-created archives**, can a held archive descriptor accessed through Linux `/proc/self/fd/N` keep both readers on the same inode through an adversarial path replacement, and what crucial protection does that *not* buy?

### Baseline, controls and predictions

Create A and B as different ordinary authentic r24 Builder archives with one equal-length logical file `payload.bin` but distinct known byte payloads; independently establish their whole archive SHA-256, `preflight_archive`, `verify()`, and `read()` controls. Install the exact O193 package outside source checkout and verify Reader/validation module bytes against the checkout.

1. **Ordinary two-path arm:** strict `preflight_archive(path_A)` accepts A; replace `path_A` atomically with valid B; `CMPCT(path_A)` then reads B (not A). This is an identity mismatch, **not an exploit or acceptance of malformed data**. Disproof: path remains A or Reader fails unexpectedly.
2. **Descriptor-pinned arm:** separately regenerate A/B; hold `os.open(path_A, O_RDONLY | O_CLOEXEC | O_NOFOLLOW)`; use `/proc/self/fd/<n>` both for strict preflight and Reader after adversarial atomic replacement. Predict reader inode equals held descriptor inode and reads A, while fresh opening of `path_A` reads B. Disproof: preflight cannot open fd alias, Reader follows renamed external pathname, inode differs, or payload differs.
3. **Same-inode mutation negative:** preserve a writable descriptor to old A before rename; after the pinned Reader has loaded A, modify only a header magic byte by `os.pwrite` on *the same old inode*. Predict the held fd SHA differs from its preregistered original, a fresh strict preflight rejects the changed header, while an already-open Reader may still return the previously loaded payload from its cached index/mmap. This deliberately falsifies the claim that pinning source **inode identity** also pins source **byte immutability**. If any observation differs, record it honestly; do not coerce a pass.

### Strongest alternatives and BONK decision

- Repeat the O205 generic POSIX `os.replace` primitive: cheaper but **already answered**, and cannot prove installed CMPCT behavior.
- Modify the product Reader to call preflight twice: rejected because two path opens do not establish source identity and would duplicate work without a correctness proof.
- Copy the complete archive into privately owned immutable storage before admission: stronger snapshot isolation but exports full I/O/space; do not promote without charged product evidence.
- Reuse a held descriptor through a `/proc` fd-path façade: selected **Linux-only scientific falsifier**. No claim of Windows/macOS portability, same-UID immutability, resource limits, recovery fidelity or ready-to-merge product design.

### Decision and burden

- **Identity mechanism supported** only if both actual modules use the original inode and original source bytes after a competing pathname is replaced, while the unchanged pathname arm demonstrably follows B.
- **Immutable snapshot mechanism refuted** if same-old-inode mutation is observable to a fresh hash/preflight, even if the already-open Reader can still read A. No product credit; the distinction is identity versus immutability.
- **Ambiguous** for any source mismatch, exception or incomplete receipt.
- Do not modify `src/`, `native/`, format, release law, validators, comparators, frozen benchmarks, existing evidence, O193/O205 branches or the shared Discovery state. Original research results must be preserved on failure. Any future product design must be portable, account for original mmap lifetime/truncation hazards (Issue #460), and retain all existing recovery and indexed-history guarantees.
- Scientific rung: authentic-source controlled cross-run identity court. No throughput, RSS, CI generality or release claim.
- Prospective counterfactual: the earliest useful discriminator is `fstat(preflight fd) == fstat(reader fd)`, which is insufficient without separate verification of backing-byte immutability. Record this only if observed.

**Concurrency:** before implementation confirmed open #521 owner ZIP64 Reader and #542 owner strict-admission economics; this separate branch owns **only** one Linux source-identity scientific court, not product parser/edit. A neighboring implementation claiming the same question would require reconsideration before late writes.

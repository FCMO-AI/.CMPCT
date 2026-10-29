# J24G42 — Darwin compressed xattr visibility result

Date: 2026-10-29 UTC. Research-only positive. No product mutation.

Frozen prediction commit f72b6be672a96297ee2344530ad840386894e1ba.
Installed source head b0aa1f585767e8953c4ca0ca1af495666051a92b.
GitHub Actions run https://github.com/FCMO-AI/.CMPCT/actions/runs/40873003698: SUCCESS on macOS 14.8.9 ARM64.

A real UF_COMPRESSED regular file had an empty ordinary native extended-attribute name list. Adding XATTR_SHOWCOMPRESSION revealed com.apple.ResourceFork and com.apple.decmpfs. The existing experimental #757 adapter matched the ordinary native enumeration. Separately written binary xattr controls were read correctly by both native modes and the adapter.

Source artifact 12896353649 ZIP SHA256: 74827103319cc0661305c206f4f8bcc0809ef5fd4ba8af69ffc7e8dfd6e037b2. Original JSON SHA256: bc3741e45305d29c9d51852ab80f25b0b75a08bd3f537c5d135c3f6d5211001c.

Conclusion: physical OS-managed compression attributes are hidden by the ordinary native xattr enumeration. This is not evidence of loss of logical file bytes and does not justify blindly archiving or restoring compression metadata. Only one compressed system file was inspected and no actual CMPCT archive of it was built. Full product/performance/portability evidence remains unmeasured.

Initial Engineering Evidence run 40873003739 failed on missing Public-surface check PR heading; PR text was repaired after that run. No release credit. Next action: define whether CMPCT promises logical-file fidelity or native physical APFS compression-state fidelity before considering a product change.

## Representation/ownership decision, not an automatic copying request

Apple's [listxattr(2) manual](https://keith.github.io/xcode-man-pages/listxattr.2.html) documents SHOWCOMPRESSION as exposing filesystem-compression attributes, not as a flag ordinary archive code should enable unconditionally. [APFS DECMPFS analysis (2026-06-08)](https://jtsylve.blog/post/2026/06/08/APFS-DECMPFS) distinguishes the logical uncompressed file stream from its physical DECOMPFS attribute and resource-fork payload: some compression types store their data in the attribute; others place blocks in the resource fork. Non-compressed-file resource forks may instead contain independent user data. Therefore a rule based only on attribute names, without the file's compression flag and the target filesystem's restore semantics, would mix two information owners. The cheaper safer boundary is to preserve ordinary user xattrs while treating OS-managed compression as the filesystem's physical storage implementation unless a different explicit guarantee is adopted.

The current experiment stops after its first decisive positive. No speculative ratio, CPU, retained physical bytes or decoder headroom is computed; an uncharged copy of the compressed storage into a logical-file archive cannot be credited as compression. Positive result narrows an overbroad fidelity claim, not release capability. The next decision requires a distinct preregistration if physical-layout preservation becomes an authorized product objective. No discovery policy update is warranted from one specimen.

## Follow-on evidence integrity

A detached post-run receipt auditor checks actual UF_COMPRESSED, native set difference, control identity and outcome arithmetic. Seven synthetic receipt mutations (wrong source, false outcome/positive, missing compression flag, forged name difference, false provider and failed control) were locally rejected. The original hosted ZIP and JSON were rehashed independently; this does not substitute for a second kernel implementation or a complete CMPCT parser. Old and final HEADs must not share exact-head result claims.

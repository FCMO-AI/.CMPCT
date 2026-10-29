# J24G42 — Darwin compressed xattr visibility result

Date: 2026-10-29 UTC. Research-only positive. No product mutation.

Frozen prediction commit f72b6be672a96297ee2344530ad840386894e1ba.
Installed source head b0aa1f585767e8953c4ca0ca1af495666051a92b.
GitHub Actions run https://github.com/FCMO-AI/.CMPCT/actions/runs/40873003698: SUCCESS on macOS 14.8.9 ARM64.

A real UF_COMPRESSED regular file had an empty ordinary native extended-attribute name list. Adding XATTR_SHOWCOMPRESSION revealed com.apple.ResourceFork and com.apple.decmpfs. The existing experimental #757 adapter matched the ordinary native enumeration. Separately written binary xattr controls were read correctly by both native modes and the adapter.

Source artifact 12896353649 ZIP SHA256: 74827103319cc0661305c206f4f8bcc0809ef5fd4ba8af69ffc7e8dfd6e037b2. Original JSON SHA256: bc3741e45305d29c9d51852ab80f25b0b75a08bd3f537c5d135c3f6d5211001c.

Conclusion: physical OS-managed compression attributes are hidden by the ordinary native xattr enumeration. This is not evidence of loss of logical file bytes and does not justify blindly archiving or restoring compression metadata. Only one compressed system file was inspected and no actual CMPCT archive of it was built. Full product/performance/portability evidence remains unmeasured.

Initial Engineering Evidence run 40873003739 failed on missing Public-surface check PR heading; PR text was repaired after that run. No release credit. Next action: define whether CMPCT promises logical-file fidelity or native physical APFS compression-state fidelity before considering a product change.

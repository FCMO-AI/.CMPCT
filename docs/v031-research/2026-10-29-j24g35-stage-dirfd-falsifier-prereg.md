# J24G35 — private staging directory versus fd-anchored namespace custody

Date: 2026-10-29 UTC  
Status: **SCIENTIFIC FOLLOW-UP; NOT PRODUCT CODE, NO RELEASE CREDIT.**  
Parent: J24I09 negative owner [#726](https://github.com/FCMO-AI/.CMPCT/pull/726), exact `78fda13e48db0a4ce8d9f3f824ef65c0e7f9bec7`; candidate #723 `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`. Published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24.

## Why this question is different from #726

[#726](https://github.com/FCMO-AI/.CMPCT/pull/726) already **confirms** that a closed sibling mkstemp pathname can be replaced before unmodified Builder writes to it. Do not rerun that question. A natural cheap attempted repair is to move the stage into a randomly named mode-0700 subdirectory under `dst.parent`, then keep using absolute pathnames for build/verify/replace. Does that *actually* prevent an actor authorized to mutate directory entries in `dst.parent` from relocating the private directory and rebinding its original name to a symlink? If not, can directory-FD-relative create, read and rename preserve the originally selected filesystem inode even after that ancestor name changes?

This tests an **ownership/namespace primitive**, not actual CMPCT integration. A positive OS-primitive result is only a design candidate; it cannot remove #726's product veto.

## Prior evidence (do NOT misrepresent as prospective)

Before this GitHub preregistration, a local Linux OS-only test was run on 2026-10-29 UTC under root, with both same-UID and distinct-UID (65534) simulated actors. It observed `PRIVATE_DIR_ALONE_FALSE__DIRFD_PRIMITIVE_SURVIVES`. Source and original JSON were retained locally. This outcome was **known before** the present record. Accordingly this preregistration does **not** claim novelty or blinded prospective confirmation of the Linux result.

## Frozen hosted replication and disproof criteria

1. On Ubuntu 24.04 under the ordinary runner, then independently under root with a different-UID actor, create *only synthetic scratch paths*. Create a mode-0700 private directory under a mode-0777 destination parent and retain an O_DIRECTORY / O_NOFOLLOW fd.
2. An actor with permission to rename entries in the **parent** renames that private directory without traversing it, then binds the old directory name to an attacker-controlled symlink directory.
3. Legacy open and publication through `old-dirname/payload` must resolve the attacker directory (explicit negative), while `os.open('payload',dir_fd=stagefd)`, duplicate-fd write/read, and `os.replace('payload',dst,src_dir_fd=stagefd,dst_dir_fd=parentfd)` must publish exact expected bytes from the pinned original inode.
4. Independently run the same ordinary-user OS court on macOS 14 if `dir_fd` is available. Unsupported platform means **UNMEASURED**, never success. Retain machine-readable receipt and exact Git SHA. Any security identity mismatch, unexpected outside write on anchored path, or unsupported safe primitive is **FALSIFIER**, not a green success.
5. An archive export or real compaction performance, Builder/Reader integration, Windows handle semantics, same-UID malicious writer within a private stage directory, or races after a name check are **not credited**.

## Alternatives and product consequence

A randomized sibling name has already lost to #726. A private subdirectory alone is cheaper than an FD-based interface but lacks a proof when the parent name can be rebound. The stronger ownership model separates directory-entry names from open directory/file identities. A credible product continuation requires source-FD-bound Builder writes, Reader verification of that same inode, and fd-relative final publication under pinned destination parent, without silently regressing Windows/macOS. Retained directory modes do not grant security against another actor operating under the same Unix UID. No PR merge, no modification to `src/`, native, frozen tests, benchmark law, version, format, Discovery STATE, or another owner's branch.

## Counterfactual

Had the existing #726 research immediately included a directory-renaming test against mode-0700 stage subdirectories, the cheapest conventional repair could have been rejected before implementation. Test portability and root/nonroot actor preconditions independently; do not extrapolate one primitive into a product guarantee.

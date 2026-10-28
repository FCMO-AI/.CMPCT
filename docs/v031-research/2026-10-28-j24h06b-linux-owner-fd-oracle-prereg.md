# J24H06b — Prospective cheap Linux syscall oracle for authenticated hardlink *source* ownership

**2026-10-28 UTC — hypothesis locked before experiment implementation or result.** Subordinate to already falsified J24H06 real-Reader source-path race. Exact unchanged Reader/Builder parent of #629; this is *not* a parallel Reader fix or a release-evidence claim. No product-source mutation, release gate change, or new long-lived issue needed.

## Motivation / prior and novelty

[#557 J24F11](https://github.com/FCMO-AI/.CMPCT/pull/557) already proves Linux *destination* anonymous `O_TMPFILE` descriptor-to-name create-only publication; [#566 J24P03](https://github.com/FCMO-AI/.CMPCT/pull/566) already falsifies late *named-stage* replacement under a directory writer. Those mechanisms cannot be relabeled as a guarantee for **hardlink source owner** identity, whose pathname can be swapped after `isfile/islink`.

**Question:** On a nonprivileged Linux container with `/proc` mounted, can a *trusted opened regular-file descriptor* refer to the original owner inode when its pathname is removed and replaced by a symlink to a foreign file, and can a genuine `linkat` kernel operation create a hardlink to that descriptor's physical inode (without using the substituted pathname)?

## Prospective controls, alternative, kill

- Create three actual small regular files in a private tempdir (trusted owner, independent foreign sentinel, a holder). Open trusted owner by `os.open(O_RDONLY|O_CLOEXEC|O_NOFOLLOW)`, capture `fstat(dev,ino)`, then rename original owner out of its path and symlink old path to foreign sentinel.
- **Weak matched control**: ordinary `os.link(original_path, alias)` and inspect `lstat/stat/inode/SHA`. This is expected to link symlink on Linux, rather than authenticated old owner.
- **Candidate A**: Linux `linkat(owner_fd, "", dir_fd, "alias_fd", AT_EMPTY_PATH)`. Capture `errno` and success; it may need privileged `CAP_DAC_READ_SEARCH` depending on kernel/fs even though the source fd is open. Failure cannot be reframed as a general impossibility.
- **Candidate B**: Linux `linkat(AT_FDCWD, "/proc/self/fd/<owner_fd>", dir_fd, "alias_procfd", AT_SYMLINK_FOLLOW)`. This is explicit Linux/procfs feature not portable across OSes.
- Positive must preserve owner FD `fstat dev+ino` and exact trusted SHA despite substituted pathname; external sentinel byte SHA must remain unchanged; repeated same alias must return EEXIST rather than overwrite; avoid assuming flags are supported.
- **Falsifier:** B cannot be executed without privileges, links a foreign inode, modifies external sentinel, or succeeds only by using unchecked path; then retire this exact unprivileged Linux route under tested environment. If A works it is simpler; if A fails and B works, document Linux feature/dependency and resource/security boundaries. Both may fail.
- Run locally on actual Linux kernel; print OS/uid/proc mount and all syscall errno/identity/bytes. No OS mocks, no mutation outside `TemporaryDirectory`. Do not infer original installed CMPCT integration, non-Linux behavior, bounds, release safety, or performance.
- **Do not conflate** positive native micro with full-tree race safety: attacker can still rebind destination parent/final after alias publication, and an actor with persistent write access can mutate output after extraction returns. Full contract needs a trustworthy namespace authority and platform fallback, plus actual product and hostile CI.

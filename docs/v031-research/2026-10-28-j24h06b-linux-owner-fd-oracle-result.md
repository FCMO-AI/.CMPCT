# J24H06b — Linux FD-owned hardlink-source syscall oracle result

**Prospective question:** [J24H06b prereg](2026-10-28-j24h06b-linux-owner-fd-oracle-prereg.md), Git commit `13070bc917b8954ab19cd365d1de2c4e94c529c2`, committed before implementation/results. **Tier:** local actual-Linux-syscall micro/oracle, **not** CMPCT Reader product CI, cross-host proof, release credit or universally secure output-tree publication.

## Actual environment, source custody and controls

- Execution UTC 2026-10-28, local container Linux `6.18.55-x86_64-with-glibc2.41`, UID 0 then re-executed under **real UID 65534 `nobody`** through `runuser`; `/proc/self/fd` present; scratch filesystem `st_dev=27`; whole experiment confined to a temporary directory. No GitHub Actions run for this subsidiary Linux oracle.
- Local Python/ctypes test source: `/mnt/data/j24h06b_linux_owner_fd_oracle.py`; SHA256 of actual source **`3e04c3b6db7c8a55f19b7ef4671e9c1058e2cc0b86029bbd98bdfa4ff9210fde`**. UID-65534 JSON observation SHA256 **`f193f552ad63180188d633f5bf0cba32f1b58750532c8c85aca73184ccebaa69`**. These are LOCAL evidence identifiers; they do not assert a separately retrievable GitHub ZIP receipt or source-bound CI.
- Original owner regular file opened with `os.open(O_RDONLY|O_NOFOLLOW|O_CLOEXEC)` and physical `fstat(dev,ino)` saved. Original pathname then renamed aside and replaced by a symlink pointing to a different regular file. Real `os.link(original_path, weak_alias)` control created an alias that was itself a **symlink** to the foreign file (wrong original owner content). The open fd continued referencing the original authenticated owner inode.
- Two POSIX `linkat` Linux-specific routes tested with actual libc calls (no mocked OS return): **A:** `linkat(owner_fd, "", destination_dirfd, "fd_empty", AT_EMPTY_PATH=0x1000)`; **B:** `linkat(AT_FDCWD=-100, "/proc/self/fd/<fd>", destination_dirfd, "fd_proc", AT_SYMLINK_FOLLOW=0x400)`. Both returned **0/SUCCESS under UID 65534**. Their new aliases were regular files with exactly the trusted `fstat` physical dev+ino and exact trusted payload SHA, *not* the symlink replacement or foreign inode. Both second calls to occupied targets returned `EEXIST=17`, and the foreign sentinel SHA was unchanged.

## Exact local uid-65534 discriminator

| Check | Observation | Decision |
| --- | --- | --- |
| UID and platform | 65534 / Linux 6.18.55, scratch device 27 | unprivileged local kernel only |
| Signed-owner physical inode | `1573013` | held by open fd after original path rebound |
| Foreign physical inode | `1573014` | distinct from trusted |
| Weak regular `os.link(path)` | output symlink inode `1573015`, resolves foreign hash | unsafe control reproduced |
| `AT_EMPTY_PATH` owner fd | `0`, alias inode `1573013`, regular | **true owner preserved** |
| `/proc/self/fd` + `AT_SYMLINK_FOLLOW` | `0`, alias inode `1573013`, regular | **true owner preserved** |
| Occupied alias retry | `errno=17 EEXIST` for both | fail closed, no overwrite |
| Trusted SHA256 | `0368c432d0714386b6f2e631f88247fb2603eba5140b09a0644fac693cd62839` | exact after both successful FD links |
| Foreign SHA256 | `1b7bb4a8c2a47242b4f77a4349c3d337a40e062dbd0257226cf9ac253dea3cf2` | unchanged |

The two observed candidate routes create a *new hardlink to a stable physical inode* in this local supported Linux mount and user regime, rather than trusting a mutable source pathname. They therefore **falsify** the narrow idea that the identified hardlink source-identity race is unavoidable on this Linux environment. They do **not** solve it in the installed Reader because the product code was not modified.

### Reproduction kernel (Python ctypes, Linux)

```python
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
libc.linkat.argtypes = [
    ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
    ctypes.c_char_p, ctypes.c_int,
]
libc.linkat.restype = ctypes.c_int
# srcfd: os.open(authenticated_owner, O_RDONLY|O_NOFOLLOW), held open
# dstfd: os.open(owned_directory, O_RDONLY|O_DIRECTORY)
# after original pathname is swapped to a foreign symlink:
assert libc.linkat(srcfd, b"", dstfd, b"authenticated-alias", 0x1000) == 0
# Independently check os.fstat(srcfd).st_ino == os.stat(
#     authenticated_alias, follow_symlinks=False).st_ino
# plus dev, file type and full SHA. A second link to the same
# destination returns EEXIST, not an overwrite.
```

**Limits / self-critique:** This was a local single-kernel micro, not a genuine installed CMPCT extraction run or hosted macOS/Windows trial. Using `/proc/self/fd` requires procfs and may be disabled in sandboxed deployments; `AT_EMPTY_PATH` permission and support differ across filesystems/kernels/credentials. The trusted source fd must itself be obtained from an authenticated physical owner and must remain open at publication; merely opening a replacement pathname afterward would pin the *wrong* inode. A symlink/parent swap of the destination or hostile mutation after success remains possible even if this source-side race is removed. Holding every owner fd throughout a huge extraction costs O(owners) descriptor resources, so a real design must bound fd lifetime and preserve authenticated inode identity across aliases. No portable equivalent is established by this single Linux experiment.

**Counterfactual product decision:** Stop searching for more pathname checks. Reuse existing Linux owned-inode work [#557](https://github.com/FCMO-AI/.CMPCT/pull/557) and existing negative [#566](https://github.com/FCMO-AI/.CMPCT/pull/566), then conduct the cheapest **genuine Reader integration** of the fd-owned hardlink source under the **unchanged J24H06 control and hostile schedule**, with directory-root ownership and fail-closed unsupported-platform behavior. Existing #629 valid fresh-directory three-host receipts are not weakened. No source-owner branch was mutated, no release/format change, no policy self-modification, and no product-win credit.


## Primary cross-platform authority (researched on 2026-10-28 UTC)

[Apple Developer Forums thread #850377, titled *macOS/APFS: Is there a supported way to create a hard link from an open file descriptor without pathname substitution?*](https://developer.apple.com/forums/thread/850377) contains two specific answers identified as **Apple DTS Engineer, CoreOS/Hardware**. The first states that macOS does **not** currently provide the requested supported public descriptor-source hardlink API, and instead illustrates `fgetattrlist` / physical FSID/file-ID/link-count checks to **detect** a mismatch. A subsequent answer clarifies that neither ordinary link nor rename avoids the source pathname replacement problem and that sharing uncontrolled write authority over a directory fundamentally prevents promising it can never be modified during/after the operation. The engineer recommends defining concrete actor ownership and publication guarantees rather than treating additional pathname checks as atomic protection.

**Impact on current scientific frontier:** the Linux UID-65534 linkat success is a **platform-scoped feasible mechanism**, not a cross-platform proposal. macOS has documented absence of the same public fd-to-hardlink primitive according to Apple staff; the correct product fork must explicitly choose/establish a trusted output namespace (possibly controlled private staging + trusted publication), a narrowed contract with fail-closed unsupported cases, or an independently tested native implementation. Clone-by-fd is not equivalent to preserving hardlink physical inode identity. Other systems and macOS filesystem versions remain product validation work.

Microsoft's primary [FILE_LINK_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_link_information) DDI specifies NTFS creation of a hardlink using an existing source **file handle** via NT file-information operations; this is a possible OS-specific architecture lead **only**, not a demonstrated user-mode Win32 API path. The user-mode support/rights/path-rooting and real-run proof remain unmeasured.

**Counterfactual and explicit assumption:** a determined actor with persistent write access can replace aliases *after* any atomic extraction even if the extractor was correct at publication instant. Therefore the requested security property must specify exactly *when* output authenticity is guaranteed and which actors can mutate the namespace. A legitimate untrusted-origin archive and a destination writable by an adversary are different threat models; treating the latter as automatically protected by archive verification is unsound. This is a domain-contract lesson, not permission to weaken integrity or safety requirements.

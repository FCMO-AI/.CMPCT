# O47 — Win32 DirEntry stat hardlink loss: prospective product repair

Date: 2026-10-25 UTC. Status: preregistered before modifying product.

## Verified base and negative
Canonical main `80c358f8824ec1b20d349c92ed94c898090969b0` / unreleased v0.31 development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` share Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Source `Builder.scan()` uses `e.stat(follow_symlinks=False)` from `os.scandir` and only registers aliases when `st_nlink>1`. Independent O46 [run 40155875571](https://github.com/FCMO-AI/.CMPCT/actions/runs/40155875571) showed genuine installed Builder/Reader from this source physically linked input files, but Windows extraction created physically distinct outputs (Linux/macOS preserved identity). No premature causal claim from runtime failure alone.

External primary source: [CPython 3.11 os.DirEntry.stat documentation](https://docs.python.org/3.11/library/os.html#os.DirEntry.stat) explicitly specifies that on **Windows** `st_ino`, `st_dev`, and `st_nlink` from `DirEntry.stat` are always **zero**; use `os.stat()` for these values. This is a direct, specific mismatch with Builder's physical-inode ownership algorithm. O46 has separate branch and a diagnostic-receipt retry; preserve original failure.

## Falsifiable product hypothesis
For regular files on `os.name == 'nt'`, use `os.stat(e.path, follow_symlinks=False)` **before** nlink/inode decision; leave symlink and directory admission semantics intact and all POSIX paths bit-exact. Expect true Win32 physical aliases to be serialized as K_FILE owner + K_HARDLINK references, independently equal-byte regular copies to remain K_FILE, same-host SHA verified, read/extract preserve contents and physical identity. A Windows original-source Builder paired with true source hardlinks but distinct extracted file identity, an accidental copy-as-link, any non-Windows change, malformed archive accepted, or a missing full authentic wheel court falsifies this claim.

## Controls and exported cost
- Positive: at least two source hardlink aliases, a separate equal-byte copy; source physical ownership confirmed with `os.path.samefile`.
- Negative: identical bytes not same inode may **not** become hardlinked; no source/destination escapes or symlink mutation.
- Repeat-build determinism and complete archive SHA/physical sections; baseline Win32 no-hardlink bug must be preserved as historical negative.
- Protect original archive revision 24, on-disk records, Reader, validators and original zero-byte/5%-AND-3ms gate semantics.
- On Win32 regular files, an extra os.stat filesystem syscall per file is exported CPU/I/O/latency cost. Measure end-to-end on an installed-host runner; report if not measured and do not market a free fix.
- POSIX unchanged; Windows-specific strong filesystem API may be supported on local NTFS but no global ReFS/network/storage promise.

## Coordination
This is a new **distinct Builder source ownership** lane, not O43 (#397) which proves native Windows extraction from an independently authored signed archive. O46 (#400) retains the failing original Builder research. O31/O38 Reader code and all other owner branches unchanged. One compact product edit, new focused adversarial test, dedicated hosted CI if needed, then full inherited gates. No v0.30 release mutation, version bump, merge, or release without owner adjudication.

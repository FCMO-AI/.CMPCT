# J24I11 — Win32 cross-API stat identity falsifier (append-only result)

Date: 2026-10-29 UTC
Evidence class: **installed product negative / cause narrowed**, not a completed product repair.
Prediction frozen before edit: `docs/v031-research/2026-10-29-j24i11-win32-hardlink-census-prereg.md`, commit `3745426833081f9a15f13d14002b7555dbe8632c`.
First implementation SHA: `30350f931d89804bdf233c84641026298c265bd4`.
Original hosted run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40819229932

## Measured direct result
The new installed-wheel topology court passed Ubuntu 24.04 and macOS 14, failed Windows Server 2022/Python 3.11 at `Builder.scan` **before archive creation**. The exact Windows traceback is `OSError: source file identity changed during hardlink census: .../a_owner.bin`; the error was caused by the newly added comparison of `(st_dev, st_ino)` from `DirEntry.stat(follow_symlinks=False)` and `os.stat(follow_symlinks=False)`. The input was generated just before scan with one regular file, one genuine hardlink, one byte-identical independent copy and one relative symlink. Both real source inode identity checks completed before the throw. The Windows job is therefore a genuine **non-pass of the first implementation**, while the other two jobs are positive for only that first HEAD.

## Causal alternatives and corrected experimental design
The original #729 failure establishes that `DirEntry.stat.st_nlink` is not a complete Win32 link census, even when `os.stat` has a positive link count. The first J24I11 version further assumed those APIs expose identical inode ID encodings. The hosted failure disproves that *universal guard* under this Windows host; it does not demonstrate that a genuine source file was concurrently replaced. The two APIs can give different IDs for the same stable path, so the full stat's own `st_nlink` and its own inode ID should be consumed as a consistent pair. Preserve cheap regular-file type and exact-size cross-checks and nonfollowing semantics. Do **not** claim this stat pair yields a race-free source snapshot.

The follow-up product edit removes only the cross-API ID equality assertion and keeps positive link count, no-follow, type/size consistency and existing inode-first owner logic. The court now separately records `os.stat` and `DirEntry.stat` identities for the same owner and maintains the absolute invariants that a physical hardlink must extract to one inode while an equal-byte independent copy must remain a different inode.

## Counterfactual / prospective lesson
A synthetic same-path two-API `st_dev,st_ino,st_nlink` witness **before** adding an identity comparison would have predicted whether the guard was valid, at a fraction of whole installed matrix cost. This is a local experimental design lesson, not enough repeated evidence to revise the Discovery Engine or any authority/format/release rule.

## Decision now
`CROSS_API_INODE_EQUALITY_GUARD_FALSIFIED`; the candidate product repair remains **UNPROVEN** pending exact-head three-host court and source-independent physical witness. The initial negative is retained with original run identity; no threshold, workload, quality gate or archived experiment was altered to rescue it. Product release and staged-name custody decisions remain blocked by independent issues. See PR #730 for the exact candidate branch and subsequent results.

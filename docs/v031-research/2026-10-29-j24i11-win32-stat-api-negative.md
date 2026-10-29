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

## Later concurrency reconciliation: historical O47 already owns the product repair

After J24I11's initial negative and narrower retry, a broader **all-state PR/branch lineage** search identified [PR #401 O47](https://github.com/FCMO-AI/.CMPCT/pull/401) from 2026-10-25. O47's product source already implements a nonfollowing full Windows `os.stat` census in Builder and its hosted exact-head [run #40156468439](https://github.com/FCMO-AI/.CMPCT/actions/runs/40156468439) passed the real installed source/Reader hardlink + independent-copy test on Ubuntu, macOS, and Windows (2 cases per platform). Its official performance deep job was skipped; no whole-product economics credited. This supersedes J24I11's novelty hypothesis and is a stronger simpler control.

**Retirement/convergence decision:** Do not maintain J24I11 as a competing Win32 Builder fix or tune the speculative fallback after recognizing historical proof. Instead, the active J24I11 child branch **transplanted the existing O47 physical-identity code fragment** into the #725/#728 private-compaction lineage and retargeted the scientific question to integration with compaction, independent extraction inode topology and same-input Win32 creation cost. The new branch/PR #730 is explicit test/composition evidence and remains draft. Original O47 branch/PR is untouched; the initial J24I11 negative is unchanged. Original product donor is not a result of J24I11, and no new compression/format claim is earned.

**Counterfactual discovery lesson (evidence-backed, local):** A query for already-open **and historical open/closed** PR/branches covering `DirEntry.stat` + `os.stat` + Win32 hardlink before implementation would have prevented duplicate product edits and their CI costs. The Discovery Engine already includes "search merged and closed lineage" as process knowledge; no second policy rewrite is warranted. New result is the owner collision and productive reuse of O47 as a control, not a new discovery-policy invention.

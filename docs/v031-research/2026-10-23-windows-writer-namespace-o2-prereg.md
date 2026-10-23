# Windows Open-Handle Namespace Rebinding — O2 Preregistration

**2026-10-23, PRE-RESULT.** Stacked independent research experiment; no product files, release claims, or owner modifications. O0 O1 are prior positive primitive/append results, NOT a promise of replacement safety.

## Question
When a Windows Writer holds an `O_RDWR|O_APPEND` file descriptor and an optional far-out-of-file `msvcrt.locking` byte-range lease, can a **separate process** replace its archive pathname with an independently created inode? If it can, the active lease on the old inode must not be mistaken for namespace ownership; if not, identify whether the obstacle is the open handle's ordinary share mode or the sentinel lock itself.

## Controlled comparison / disproof
Same synthetic short `CMPCT24\0`-headed source and distinct replacement content, independent `os.replace` subprocess:

- **C0 no held descriptor:** replacement MUST succeed, or environmental setup is invalid.
- **C1 held O_RDWR|O_APPEND descriptor but NO range lock:** record success or Windows error, and source/target hashes/inodes. This is the **necessary control** to avoid falsely attributing Windows share-mode denial to the lock.
- **C2 same descriptor plus sentinel exclusive byte-range lock at `1<<60`:** record independent pathname replacement and, if possible, independent new-path sentinel acquisition. Record old held-fd identity, old hardlink alias, destination inode, hashes, file contents, and errors.
- If replacement succeeds under C2, it demonstrates **split namespace/physical lock ownership** and is a red against trusting `flock`/range-lock alone. If denied under C1 and C2, limitation is mostly **open handle sharing mode**, not lock specialness; it does not prove universal safety against different Win32 FILE_SHARE_DELETE openings, reparse points, noncooperative processes, or SMB.

No weakening of tests if provider returns unexpected behavior. Distinguish observed refusal from cross-platform correctness. No synthetic filesystem changes outside temporary dir. Core Writer still fails closed on Windows; no product code changed.

## Alternatives
Assume POSIX TOCTOU transfers unchanged (no evidence); assume Windows open is a namespace lease (overclaim); implement Win32 FileId locking architecture now (too broad before cheap kernel test); **chosen** held-open vs held-open+sentinel fresh-process os.replace control, preserving both directions.

## Expected decision
A replacement denial narrows the local Windows namespace risk model, while an allowed replacement demonstrates need for explicit identity validation before/after operations. Either result tells the owner what Windows-specific test family to require before porting. No native/product/release credit without actual CMPCT Writer on Windows.

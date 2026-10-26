# O167 — Windows no-follow mtime restoration: prospective hypothesis (2026-10-26)

## Authority and baseline
Released CMPCT v0.30.0, physical r24. Independent O102 (#457) is a negative witness: the unchanged O69 Reader (#425) catches Windows `NotImplementedError` from `os.utime(...,follow_symlinks=False)` and silently leaves restored regular-file and directory mtimes wrong by years, while source timestamps and logical bytes are authenticated. Inherited O69 source is `8fe424ac8575da10bf5ecfdb9660d4b5831f638b`. O102 scientific control and its expectations are frozen and must not be changed. No existing product owner was identified for this exact Win32 timestamp repair.

## Primary falsifiable question
Can a small, Windows-only `CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT|FILE_FLAG_BACKUP_SEMANTICS)` + `SetFileTime` handle-bound fallback restore authenticated file/directory mtimes to within 3 seconds on Windows 2025 without following a **final-component** reparse point and without modifying POSIX behavior or the optional strict xattr contract?

## Competing mechanisms
1. `os.utime(path)` default following links: simpler but rejected because a destination symlink/reparse pivot could write metadata to an external target.
2. Suppress `NotImplementedError`: current portable behavior; keeps a known year-scale fidelity loss.
3. Win32 non-follow handle with explicit `FILE_ATTRIBUTE_REPARSE_POINT` rejection and type check: selected bounded implementation, without new dependencies.
4. Full trusted dirfd/walk custody: stronger for mutable ancestor components but outside this narrow portability fork and overlaps broader namespace work.

## Preregistered decisive evidence
- Use authentic Builder r24 archive from a disposable 2020-stamped source regular file and directory, verify serialized timestamps and reader payload/hash, run `extractall(metadata=True)`, and inspect **physical** file/dir `st_mtime_ns` within 3 seconds. Test on Windows 2025 and POSIX unchanged.
- On Windows independently exercise the low-level helper directly against a regular file/directory and, when supported by the host, a final-component symlink whose external target timestamp must remain identical and whose handle should reject reparse.
- On Linux/macOS the helper is not invoked; both old no-follow behavior and source physical timestamps remain accurate.
- Preserve raw JUnit/JSON, installed-package source custody, exact candidate SHA, original O102 negative unmodified. Any Windows metadata loss, unexpected target write, incorrectly accepted final reparse point, source/reader mismatch, xattr-default regression or CI integrity failure narrows/falsifies this candidate.

## Limits and economic debt
The proposed Win32 handle binds the **leaf** opened by the OS, but does not establish a trusted full ancestor walk. Hostile ancestor directory replacement, source/destination hardlink aliasing, junction traversal in ancestors, power-loss durability, ACL/xattr semantics and true tree-wide atomic publication remain unproven. Setting timestamps requires one additional Win32 handle open per file/dir on unsupported-no-follow hosts, so performance/no-regression must be measured before promotion. Format, compressor, reader payload bytes, benchmarks, thresholds, frozen historical evidence and release version stay untouched. No test green is release credit.

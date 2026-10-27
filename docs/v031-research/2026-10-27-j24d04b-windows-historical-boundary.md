# J24D04b — prospective repair of Windows historical-control boundary

**2026-10-27 UTC, recorded after first hosted J24D04 result and before altering the instrument.** Original J24D04 prediction/preregistration and original failed run remain unchanged.

## Observation requiring a narrower platform court

First hosted exact-head J24D04 scientific run [40489172441](https://github.com/FCMO-AI/.CMPCT/actions/runs/40489172441) at `b2418c75ce15115ba7d9d0722549e35d626ad320`:

- Ubuntu job `122138477109`: success, all 24 genuine original/candidate direct RAW/Zstd/Deflate source checks. `metadata=False` with `umask 0o077`: released Reader mode `0o600`, candidate `0o644` in all three codes; alias/inode and `metadata=True` controls pass.
- macOS job `122138476718`: same 24/24 and same source-dependent permission difference.
- Windows job `122138477009`: exact original/released r24 Reader fails *before candidate observation*, when J24D04 tries `metadata=True` on RAW: unmodified Reader `os.utime(full, ns=(mt,mt), follow_symlinks=False)` raises `NotImplementedError: utime: follow_symlinks unavailable on this platform`. The original Reader only catches `OSError`; this is an **inherited Windows metadata portability negative**, not a direct-stage regression or a scientific false green.

## Narrowed, frozen follow-up

Do not edit the released Reader, frozen vector, J24D04 POSIX metrics, thresholds, source bindings or meaning of a successful result.

**On Windows only**, execute the remaining `metadata=False` cases: fresh file, existing file, and external hardlink alias, all three unchanged RAW/Zstd/Deflate golden vectors, both installed exact Git source packages: 18 checks. The `metadata=True` check is unavailable for the original Reader and must be reported separately as a **known observed original-source failure**, not silently declared passing. Keep the full four-case 24-observation trial on Ubuntu and macOS.

Independent receipt referee must enforce exactly 24 on POSIX or exactly 18 on Windows, complete uniqueness, archive/input/output SHA, no leaked stage, and all POSIX permission/inode/alias assertions unchanged. On Windows do NOT assert POSIX umask/permission equality; run exact output/SHA and source identity only.

**Disproof:** any incorrect goldens, absent source identity, wrong file hash, stage leakage, unexpected behavior of a supported Windows metadata=False case, or lost POSIX negative invalidates the repaired court.

This addendum is prospective relative to the revised experiment only; it does not overwrite or retrospectively rename the first Windows failure. No product promotion from either result. Document the inherited NotImplementedError as a separate release/portability debt for the Reader owner.
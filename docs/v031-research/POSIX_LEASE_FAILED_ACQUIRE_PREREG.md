# O4 — failed writer lock acquisition must preserve original errno

Date 2026-10-23; preregistered before test and product mutation. O3 Writer source `27c8e7003d3f02c28b63be8cff6debc134dde86d`. Current lock context calls `LOCK_UN` in `finally` even if `LOCK_EX` failed; the unlock might itself raise an unrelated exception and mask the real acquisition failure. This is particularly relevant when the storage provider rejects `flock` or resources run out.

**Prediction:** Under an isolated injected lock provider whose `LOCK_EX` fails with `OSError("injected acquisition failure")` and whose `LOCK_UN` would fail with `OSError("unexpected unlock after failed acquisition")`, original current code masks the acquisition cause. Corrected code must track whether lock acquisition succeeded and never call `LOCK_UN` before success; it must still close the opened fd in all outcomes, reject mutation before snapshot, preserve existing archive bytes and expose the original exception.

Only the sequence of injected syscalls changes. Stronger control is previously hosted full public mutation tests; no change to format, release gate or historical benchmark. This is a narrow resource/diagnostics issue, not proof of NFS/Windows parity or process crash. Keep all negative logs; repeat exact-head test after fix.

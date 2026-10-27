# J24D04c — independent referee initialization defect (before repair)

**2026-10-27 UTC; preregistered repair after outcome, before referee modification.** Original J24D04, first hosted result, and J24D04b remain immutable.

GitHub Actions [#40489908325](https://github.com/FCMO-AI/.CMPCT/actions/runs/40489908325) at `84fed7849d6959ffca1d9bc23c5eb8939c9697dd` completed all 18 supported Windows actual historical/candidate source observations; the independent referee fails with `UnboundLocalError: os_name` in a case-count assertion because the J24D04b code references `os_name` before assigning it. Ubuntu/macOS share the same referee failure. This is **experimental auditor code**, not tested product semantic divergence. The original output/negative must not be discarded or retroactively called passing CI.

**Narrow proposed repair:** bind `os_name` immediately after the existing checked singleton `os_names` set at the top of referee `check()`, before the case-count and all other uses; keep full 24 POSIX / 18 Windows constraints, original/candidate source fingerprints, encoded inputs, mode/alias assertions, source and release code completely unchanged. Drop only redundant later assignment if appropriate.

**Kill:** any still-red referee, missing raw measurements, byte-level mismatch, weakened platform-specific case-count control or malformed evidence means the research claim remains blocked. Hosted rerun is required. No product release, discovery state, benchmark, format or safety gate changes.
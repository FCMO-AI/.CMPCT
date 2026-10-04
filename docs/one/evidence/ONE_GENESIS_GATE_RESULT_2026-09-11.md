# CMPCT1 / ONE Genesis gate result — 2026-09-11

Status: **FINAL GATE VERDICT — `REACTIVATE_V030_NEAR_TERM`**

This path is mirrored onto the reactivated v0.30 line so zero-history agents can recover the gate decision without switching branches. The full result was first persisted on `research/cmpct1` by commit `ee14383cd6309d62fed1efba2c92f48ba54ae50f`. The v0.30-line operating handoff is `docs/CMPCT1_ONE_GENESIS_GATE_RESULT_2026-09-11.md`; the causal deficit map is `docs/V030_REACTIVATION_GENESIS_DEFICIT_MAP_2026-09-11.md`.

Frozen contenders:
- ONE-G0.2 `38f17f4a45686a59a853bf62f0c840e228879e17`
- v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

All three completed 15/15 exact same-input rows. Aggregate authenticated stored bytes over `265,969,714 B` logical:
- ONE: `275,219,901 B` (`1.034779x`)
- v0.29: `137,499,525 B` (`0.516974x`)
- v0.30: `150,055,575 B` (`0.564183x`)

ONE loses density to each mature comparator on `15/15` rows. ONE creation CPU wins `15/15` against each; sum of per-workload median fresh-process creation CPU is ONE `3.0791 s`, v0.29 `806.5369 s`, v0.30 `33.0603 s`.

The source-sealed missing v0.30 matrix was recovered successfully in run `34594599804`, job `103251512822`, artifact `10263288496`, digest `sha256:1e73f88c597bf0e16f60375b2f51c0ec0a79cf8204683adb7c00dde32b44c148`, exact harness `7e14e6867a329bc3281e9016e673c46dc3feb081`. Frozen comparator source provenance is fail-closed.

Decision: v0.30 is the primary near-term research line. Preserve ONE and its compute-efficiency breakthrough as a secondary research line; do not retroactively rerun/tune the frozen ONE candidate to change the gate result.

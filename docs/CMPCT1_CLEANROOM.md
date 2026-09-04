# CMPCT1 clean-room control

Status: research control branch for CMPCT1 / ONE.

Branch: `research/cmpct1-cleanroom`

Base: canonical `main` at pivot SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` (2026-09-04).

Purpose: provide an uncontaminated control line for experiments that must answer whether a CMPCT1/ONE mechanism itself creates a gain independently of deferred v0.30 integration work.

This branch is not the primary development line and should not independently evolve into a competing architecture. Findings that survive here should be transferred as evidence or compact patches into `research/cmpct1`. The primary research line inherits the frozen v0.30 integration pivot so it can absorb prior valid work rather than recreate it.

Do not bump canonical project versions here. Use experimental ONE identifiers only. Preserve exact comparator/corpus fingerprints and negative results.

# CMPCT rolling pre-1.0 release policy

Status: **NORMATIVE — effective 2026-10-04**

CMPCT 0.x releases are rolling material checkpoints. A minor version must not remain open merely because a
benchmark target was assigned to that version.

A pre-1.0 release may publish when it contains coherent material product/research progress and its evidence
can be stated honestly. It does not need to win every frozen workload, beat ZIP/Zstd on every row, exhaust
every research lane, or close every known performance debt.

Known losses remain public evidence and roll forward as engineering targets. Benchmarks remain mandatory
as evidence, but not as a version-number prison.

## 1.0 graduation target

Under equivalent semantics and controlled same-input measurement, CMPCT 1.0 should strictly beat ordinary
ZIP/Deflate-9 and solid Zstd-19 in both complete archive size and creation wall time on **15/15 frozen
serious workloads, with no ties**.

This does not gate v0.30, v0.31, or another 0.x checkpoint. Safety, exactness, integrity, recovery,
resource bounds, portability and reproducibility remain non-negotiable.

After v0.30, development proceeds immediately on v0.31.

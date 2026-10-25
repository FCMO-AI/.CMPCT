# O108 — Reader output FIFO exposure across physical storage paths (prospective preregistration)

Date: 2026-10-25 UTC. Status: PREDICTION FROZEN BEFORE INSTRUMENT / OBSERVATION.

## Authority, baseline and concurrency
Canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; original Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, published v0.30.0, physical format revision 24. O106 #461, exact-head Actions #40225047480, demonstrated **S_BLOB** existing FIFO blocking in authentic installed Reader. Issue #462 records the open defect. Reader static destination safety #269 owns the product behavior, but its preflight does not explicitly refuse nonregular direct-write leaves. This O108 owns only independent storage-path coverage and does not change Reader, other PR branches, parser/release evaluators or shared discovery cache.

## Primary question and prediction
**Is the O106 availability defect representation-specific or caused by every Reader direct-write storage branch?** On genuine revision-24 archives with one member and the same physical archive reused across all trial destinations, an existing unconnected POSIX FIFO is predicted to hang (`>8 s` in a killable child after Reader index opened) for:
- `S_BLOB`: ordinary `os.open(... O_WRONLY | O_CREAT | O_TRUNC)`;
- `S_SPARSE`: `os.open` followed by `ftruncate`, using a real sparse source whose sparse representation is asserted;
but **not** for:
- `S_CDC`: verified temporary-file staging and `os.replace`, which is predicted to return and replace a FIFO leaf. This is a distinct filesystem-semantic difference, not automatically a universally safe behavior.

A symlink leaf pointing to the FIFO should hang on both direct-write representations and be replaced (not followed) by the staged CDC path. A pre-existing regular file and fresh nonexistent leaf must reconstruct exact original bytes for each storage mode. The FIFO must remain intact after each timed-out child. No external files outside the disposable fixture are touched.

## Stronger simpler controls / kill conditions
One real installed Builder creates each archive once; record actual `row[6][0]` and refuse to substitute a synthetic/manual index if the requested representation is not produced. One reader process per output trial, hard 8s timeout, positive same-archive read/verify and source hash, unique disposable destination. The native filesystem must support FIFO and true sparse allocation or the corresponding experiment must be reported unsupported, never a product positive. An ordinary-control timeout or inability to produce exact S_CDC/S_SPARSE invalidates the court; unexpectedly prompt FIFO rejection falsifies that arm. The same physical archive SHA must be constant *within each storage arm*, preventing corpus drift.

Alternative explanation: child import, Reader parse, archive decompression, invalid sparse fixture, or heavy CDC decode could explain a timeout. Require a child `INDEX_OPENED` marker; positive fresh and regular cases constrain non-output costs. An authenticated archive with S_SPARSE but slow decompression is not evidence of a FIFO block unless controls are promptly complete.

## Scope and costs
Scientific product negative/positive only, no shipping patch, no format change, release or claimed universal race safety. One Linux hosted installed-product court, 12 bounded child trials (3 modes × 4 leaf kinds); if portable reliable execution permits, macOS replication later. Reader I/O, inode semantics and post-check TOCTOU remain separate; no performance comparisons or product credit. The strongest follow-on for #269 is **one fail-closed direct-output-leaf guard covering S_BLOB and S_SPARSE** that preserves regular reuse and the existing CDC atomic path; a path-only guard is not full concurrency defense.

## Permanent falsification rule
Retain any surprising differences and raw child exit/timeout details. If S_SPARSE on the actual runner is unsupported, do not claim sparse hypothesis confirmed. Never tune fixture shape after observing results to rescue the preregistered 3×4 claim without recording a changed experiment. Exact-source identity and CI artifacts must accompany any conclusion.

## Evidence class
This is a branch-local prospective research contract, not a second authoritative CMPCT state database or a Discovery Engine policy change. Durable outcomes will link run ID/artifacts and negative evidence explicitly.
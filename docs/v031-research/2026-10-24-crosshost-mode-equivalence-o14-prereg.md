# O14 preregistration — cross-host reproducible archive mode equivalence

Date: 2026-10-24
Status: **PREDICTION / NO RESULT**. This document is committed before any O14 instrument, test or hosted measurement.

## Authority / baseline
CMPCT v0.30.0, revision 24, remains the released floor. Independent unreleased source for this experiment: PR #352 HEAD `93e9a00fd352ac567e9b069654aa145148370d42`. Issue #353 reports that its existing installed wheel smoke corpus reconstructs exactly on all three operating systems but baseline reproducible archive SHA-256 is `6824f2b5...` on Linux/macOS versus `3722374c...` on Windows. This is not a losslessness failure or proven encoder nondeterminism. The original smoke creates exactly two regular files and one directory with `Builder(src, workers=1, reproducible=True, reproducible_epoch_ns=0)`.

## Primary question
For an exactly identical two-file byte corpus and the same source, does independently normalizing **only the serialized file mode field** remove the Linux/macOS/Windows whole-archive SHA difference? This is an instrumented research intervention, **not** a proposed silent product-mode change.

## Mechanism and prediction
The actual `Builder.scan()` puts `stat.S_IMODE(st.st_mode)` into each row. Reproducible mode resets mtime/uid/gid/xattrs but not mode. Windows and POSIX runners may report different source modes. Hypothesis H1: observed default modes differ and a fixed-mode scanner variant (`0755` directories, `0644` regular files, only for this experiment) yields byte-identical archived indexes and complete archives on all three hosts. Simpler H0: the source modes are already identical or mode normalization fails to remove the divergence; then test native codec/backend, index/physical record or filesystem metadata next.

## Controls / rung
O14 is a cheapest product-coupled A/B: **same input bytes; same installed product, same host, same builder options**, native/default scan versus an isolated `Builder` subclass whose overridden `scan()` calls the original then changes **only** `row[2]` for directory and regular-file types. No codec, representation, evaluator, archive format, semantics or release limit changes.

For each OS, record source path/kind/lstat permissions and source SHA; complete baseline and mode-normalized archive SHA and sizes; index rows (path/kind/mode/normalized time/size/physical refs); blob/recipe fingerprints; full open, strong verify, exact member read/extract; and an on-host control that the experimental index differs from ordinary source only in mode fields. Run two independent output builds of each variant per host to catch intra-host nondeterminism. Aggregate host artifacts and compare signed tree, logical file bytes, normalized index representation and complete archive digests. Attribute the result without rewriting the original Issue #353 observation.

## Decision / kill criteria
- **H1 survives** only if normalizing modes produces identical complete archive SHA on all three hosts, and archive validity, exact content, and unchanged non-mode index/physical sections are verified. Baseline mode differences alone are insufficient.
- **H1 falsified/narrowed** if normalized complete archives still differ, if any non-mode index/record field changes unexpectedly, or if roundtrip changes. Preserve all divergences by field, not just digest.
- If baseline source mode/bytes differ across hosts, account for it before any encoder attribution.
- No release promotion, mode contract revision, new version, synthetic compression win or benchmark threshold relaxation. This test does not establish reproducibility over arbitrary filesystems, symlinks, ACLs or heterogeneous native codec versions.

## Concurrency and ownership
The previous #352 installed desktop custody owner keeps its files. This is a separate child branch for Issue #353's unclaimed cross-host archive identity question; no changes to the installed smoke, Builder, Reader, existing CI, release records or `docs/discovery/STATE.json`. Any future product proposal requires explicit portable-mode semantics, full release comparison and original mode-fidelity controls.

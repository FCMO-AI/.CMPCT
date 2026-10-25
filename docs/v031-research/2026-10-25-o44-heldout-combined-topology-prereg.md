# O44 — Non-frozen combined-corpus hardlink-topology court (preregistration)

**Status:** PROSPECTIVE HOSTED EXPERIMENT; no hosted result observed when this preregistration is committed.  
**UTC:** 2026-10-25.  
**Repository:** `FCMO-AI/.CMPCT`.  
**Exact starting source:** PR #328, `36c5c737c2896b9ad9ee68c491ff921fbd36aaa4`; `benchmarks/universal_bench.py` Git blob `2668948a64a03fc7f2b7c97fd97c8e0696aa9bee`.  
**Ownership:** Independent research-only follow-up to the O42 witness / #396; do not modify its branch, official parity corpus, `zip-parity.yml`, archived results, benchmark thresholds, or product implementation.

## Baseline / already known

The universal generator creates a source `dedup_links` subtree with `real.dat` and `hardlink.dat` sharing one inode. Its `combined` subtree uses `shutil.copytree(source, dest, symlinks=True)`; this does **not** claim to preserve hardlink equivalence. O42/#396 independently reproduced a small synthetic hardlink-vs-copy false-equality. That result is inherited prior art: O44 must add **actual-generator, root-independent, end-to-end structural evidence and a safe prospective held-out test fixture**, not just another two-file demonstration.

A four-case *local pilot* of a generic `copytree(copy_function=...)` helper passed before this hosted preregistration. It is design/debug evidence only, not a preregistered hosted result. Historical product v0.30.0/r24 and frozen benchmarks remain authoritative.

## Primary question and prediction

On a fresh real `universal.make_corpora()` output, does the combined copy lose the source's in-tree hardlink partition while retaining identical member contents and metadata? Can a separate **non-frozen held-out** combined corpus assembled using a source-inode-to-destination-file map restore that partition without silently conflating equal-byte but independent source inodes, following symlinks, or changing data bytes?

**Predicted:** `dedup_links/real.dat` and `dedup_links/hardlink.dat` are physically linked, `combined/dedup_links/real.dat` and `combined/dedup_links/hardlink.dat` are independent, and a newly generated `heldout_combined/dedup_links/` pair shares one destination inode; the original combined and held-out trees have identical relative path/type/content/symlink-target/mode/mtime snapshots. Equal-byte independent `copyXX.dat` entries stay physically independent. If source roots have linked names to files *outside* copied subtree, destination files must remain physically independent from those external names.

## Stronger controls and alternatives

- Control A: the actual unmodified `shutil.copytree(..., symlinks=True)` called by the current generator, not a new model pretending to be the original.
- Control B: independently compare root-relative hardlink equivalence partitions via `(st_dev,st_ino)` only **within each tree**; never compare numeric inodes across roots.
- Control C: compare typed relative path, file SHA-256, mode/mtime and exact symlink target rather than relying on a legacy content-only digest.
- Alternatives: modify the original generator (forbidden because it changes frozen comparison inputs); post-hoc relink by file hash (forbidden because equal-byte independent copies must stay independent); encode source inode numbers into an archive (violates portable relative semantics).

## Procedure / evidence rung

1. Build the actual official-source generator's corpora **without running or changing official performance comparison**.
2. Record immutable original source/combined hardlink partitions and typed-content snapshots.
3. Use a general filesystem-preserving copy helper on the generator's source categories to assemble a **separate, explicitly non-frozen** held-out combined corpus.
4. Run the source-exact hosted adversarial court (including symlinks, nested paths, identical-byte independent copies, cross-root independence, and a deliberately rejected non-directory root); retain raw observed fields in a JSON artifact with the exact source SHA.
5. Do not grant archive-size/performance/product credit absent subsequent separate real CMPCT-vs-competitor, same-input/same-semantics evidence.

## Falsifiers and narrowing

Retire or narrow the helper if any source link group is lost, if an independent same-byte file is erroneously hardlinked, if a symlink is dereferenced, if typed member payload/metadata differs, if source-mutating/unsupported-hardlink behavior is silently hidden, or if the original full generator already preserves the combined physical relation. A Windows/APFS outcome is **unmeasured**, not inferred from Linux success. The helper assumes a quiescent trusted benchmark corpus and is **not** an atomic or adversarial filesystem snapshot.

## Decision and costs

The expected decision is whether a future new-version held-out combined benchmark is justified to expose missing mixed-structure reconstruction without rewriting historical results. Measure additional copied physical bytes, wall time and logical/physical entry counts when feasible. If the only benefit is one fixture and equivalent existing `dedup_links` evidence already covers the question, retain the negative cost result and do not integrate a new main benchmark or new release rule.

## Concurrency

O42/#396 retains ownership of official ABBA input witness and its failing inherited blob-locked court; O44 touches neither. PR #328 remains unchanged. No second project-state cache and no `docs/discovery/STATE.json` write until a decision changes. Product/format/version/Release gate: no changes.

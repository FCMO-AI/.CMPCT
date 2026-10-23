# CMPCT v0.31 O2 — actual POSIX sparse-extents discovery, fully charged cold Merkle descriptor

**Status:** FROZEN PRE-RESULT O2 SCIENTIFIC PREDICTION; research-only, no product/release/format change.
**Date:** 2026-10-23 UTC.
**Base/owner:** PR #279 O1, exact HEAD `1a2b2577505030f2fdd4fd08063e3ba45d912374`. Independent O2 addition on a new stacked branch. Other Reader/Writer/format owners are not modified.
**Current reality:** shipping v0.30.0, revision 24; `verify` requires flat logical SHA-256. PR #270 sparse integrity performance gate failed (+~102ms) and PR #273 attributed ~93ms to flat hashing of holes. O0/O1 alternative Merkle identity is **not** r24 SHA. O1 models were given exact positions and data by a synthetic generator, which is not evidence of real source acquisition.

## Primary question
Can actual Linux `SEEK_DATA`/`SEEK_HOLE` + bounded `pread` discover enough source information to create the exact O1 research Merkle commitment for real filesystem objects while preserving all logical bytes, handling allocated zeros/partial blocks, bounding temporary RAM, charging every cold descriptor byte, and failing safely on unsupported/incoherent seek behavior?

## Hypotheses & observable predictions
1. On actual, freshly created Linux files with 128 MiB logical size and ~4 MiB clustered allocated data, the fully charged O1 descriptor should remain <= 4 KiB and its root must match an **independent whole-byte materialization**. The measured exact same-source discovery+read+Merkle+serialize wall may be < 50% of conventional flat-SHA whole-file wall; if not, retain root-correctness credit only.
2. All-hole, shifted/misaligned, allocated-zero, highly fragmented, dense, and partial-tail real files must each reconstruct exactly (both independent logical whole-file SHA/byte oracle and O1 Merkle root where feasible). At least one dense/fragmented regime should lose in index/work economics and must not be relabeled.
3. Materialization must use at most one logical leaf buffer plus bounded I/O chunks, not `O(number_of_logical_leaves)` memory; only the mandatory `O(nonzero_leaf_count)` descriptor is retained. Enforce descriptor/row/scan step budgets and explicit short-read rejection; O1's established strict descriptor parser is the independent cold verifier.
4. A sparse and an allocated-zero file may have identical logical contents and research roots but different `SEEK_*` maps. The root must not be represented as authenticating the **physical hole allocation map**. Record extent metadata separately; do not make lossless claims about on-disk allocation.
5. Unsupported `SEEK_DATA` or `SEEK_HOLE`, if simulated or observed, must fail closed or conservatively fall back to full bounded reads—not synthesize a hole without positive filesystem evidence. Invalid/stale offset progression, changed-source identity and out-of-range extents should be rejected.
6. All hidden cost is disclosed: logical size, actual `st_blocks`, data bytes actually read, extent counts, wall/CPU of discovering and assembling, descriptor bytes, cold reopen, peak Python tracemalloc, I/O/cache limitations, scan budget, and platforms unsupported.

## Strongest simpler controls and alternative explanations
- Control A: O1 `from_extents` with **gifted** positions is cheaper but has no source-acquisition semantics. Comparisons to it must not claim product economic credit.
- Control B: conventional flat SHA over the same real source fully and directly remains revision-24 identity and performance baseline.
- Control C: independent full-byte logical Merkle oracle from prior O0 is the correctness referee for moderate physical files, not the candidate's own computed root.
- Alternative: favorable results may be artifacts of Linux extent reporting, page-cache heating, filesystem block rounding or precreated local sparse fixtures. Alternate sample order and preserve raw observations; fail broad portability claims.
- Alternative: `SEEK_HOLE` is permitted to report allocated zero-filled blocks as DATA, so discovery cannot reliably avoid reading all logical zeros. Include allocated-zero and dense losing controls.

## Kill/narrow conditions
Any mismatched root; misread nonzero source byte; stale or overlapping extents accepted; unbounded allocation/loop; bypassed unsupported-seek safety; uncharged descriptor metadata; same source not used for baseline; or claim that O1 root equals r24 flat SHA retires the current implementation claim. If correctness survives but real discovery/exported cost is adverse, restrict to research seed and do not promote. If all favorable cases only result from fixture-specific Linux allocation, do not infer generic admission.

## Scope, concurrency, and next gate
Only research script, reproducible court, and append-only result on this stacked O2 branch. No modifications to O0/O1 scientific sources or to canonical `src/cmpct/*`, `docs/discovery/STATE.json`, frozen criteria, comparator, or version. Do not force push. Publish source SHA + result artifacts and exact-head CI. A future versioned proof model additionally needs source freeze/TOCTOU solution, authenticated index binding, interoperable semantics, read/selective byte accounting, recovery and mature native/fs-verity controls before product promotion.

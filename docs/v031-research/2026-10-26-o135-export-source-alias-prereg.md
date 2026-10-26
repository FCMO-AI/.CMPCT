# O135 — ZIP export must not destroy its own open CMPCT source (preregistration)

Date: 2026-10-26 UTC
Status: PREDICTION FROZEN BEFORE IMPLEMENTATION OR PRODUCT MEASUREMENT
Repository: `FCMO-AI/.CMPCT`
Exact parent: `2e493d2d941f9c144c0c5050b41c88dc7c6e57dd` (PR #284, stacked on owner PR #260).
Frozen parent Reader source blob to be recorded by CI, not inferred from this document. Published v0.30.0/r24 and historical release lock remain unchanged.

## Baseline and ownership

The source-exact PR #284 Python `CMPCT.export_zip(out)` first opens a fully valid CMPCT archive for reading/mmap, then creates/truncates `out` via `open(out, "wb")` (or `zipfile.ZipFile(...,"w")` on the large-member fallback). If `out` is the very same physical inode as the still-open CMPCT archive, either by identical pathname, hardlink, or symlink, export can truncate/destroy its own source and potentially terminate with a fatal mmap access. This is different from O118 (#468) which concerns **extractall**, from O2–O5 (#286) which concerns external mutation of a live mmap *between* verify and copy, and from PR #284's physical Deflate preflight. PR #260 owns ZIP64 count, PR #284 owns direct Deflate export verification, and PR #286 owns related mutation research. This branch owns only static **ZIP-output/source inode identity**.

## Primary question, falsifiable prediction

On the exact authentic PR #284 Reader, with one immutable builder-independent revision-24 RAW golden and one independent direct-Deflate golden, compare four modes: disjoint output, self-path output, preexisting hardlink alias, and preexisting symlink alias. Every child is a fresh isolated process, gets the same source bytes and a well-defined destination, and runs `CMPCT.export_zip(out)`. The parent independently checks the SHA-256 of the **original source after child exit**, child status (including SIGBUS), and independent ZIP member decoding for disjoint controls.

Prediction: the **unmodified** parent destroys or mutates the source archive in all six POSIX alias cases (or an otherwise demonstrable source-integrity failure), while two disjoint controls export exact member bytes. Disproof: source preservation/refusal on an alias that invalidates a blanket failure claim, or corrupted disjoint controls.

Candidate hypothesis: one early `fstat(self.f.fileno())` versus `os.stat(out)` comparison of `(st_dev, st_ino)` refuses static aliases *before* either export branch opens an output. Existing destinations unrelated to the archive and new output paths remain exportable. Prediction: all six alias cases raise managed `OSError/IOError` and preserve source bytes; disjoint controls independently decode exactly. A false reject, unchanged baseline alias, surviving candidate source mutation, corrupted output or uncaught fatal signal refutes the respective claim. The conditional large-member fallback remains structurally covered by the pre-open placement but is not exercised by a >4GiB member in this small court; no ZIP64 runtime claim.

## Controls and alternative routes

Strongest simple control is caller promise not to pass aliases; inadequate as a safe library contract. Lexical equality misses hardlinks and symlink targets. `os.path.samefile` is convenient but uses two pathname stats and can race; comparing destination stat against the already-open Reader FD is better source identity. Full staging/atomic publish could protect other outputs and reduce races but exports additional I/O and temp bytes, an owner-scale architectural redesign. Reject all preexisting paths would break legitimate overwrite behavior. Chosen guard is static and `O(1)` filesystem-stat work per call.

Concurrently hostile rename/symlink substitution after the check is **not** covered; source inode changing via an external writer is independently covered by O103/O2 research and needs genuine snapshot/descriptor-lifetime design. This proposal cannot claim race-free publication, standalone ZIP64 behavior, general performance improvement, or safety from arbitrary mutating inputs.

## Cheapest evidence / source custody / stop condition

First commit this immutable prediction. Then add a small differencing pytest court and branch-scoped workflow executing both **real historical source** and exact candidate without changing the parent. Bind both Reader file blobs, exact Git commit SHA, frozen golden SHA-256 and raw child results. No test/model/evaluator changes after seeing evidence to rescue a preferred outcome. An unexpected baseline result narrows the claim honestly. Run basic install/import/parse checks and, if hosted work cannot execute, report that as an infrastructure blocker, not evidence. Preserve CI checks and non-green scope transparently.

No public version bump, reader/on-disk format change, release promotion, threshold gardening, frozen benchmark rewrite, or edits to active owner branches. Notify export owners with final evidence and remain draft until performance, portability, safety composition and source-integrity gates pass.

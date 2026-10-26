# O132 preregistration — macOS sparse fixture mode divergence

Date 2026-10-25 local / 2026-10-26 UTC. Science-only; do not alter products or inherited evaluators.

## Authority and baseline
Shipping CMPCT v0.30.0/r24; v0.31 canonical branch 4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b. The independent diagnostic is stacked on unchanged parent PR #294 at 700fa74df7d9101b3d00322ab5b3606ee64faf88. Owner PRs #472/#479 retain one unchanged inherited macOS test failure (8/9): test_v031_destination_hardlink_leaf_alias.py [sparse] expected S_SPARSE in the generated archive before any Reader destination safety assertion, while Linux 9/9 passes. Hosted evidence: https://github.com/FCMO-AI/.CMPCT/actions/runs/40246773131.

## Primary falsifiable question
Which physical filesystem sparse eligibility fact makes the original seek-and-write 16 MiB fixture fail to select S_SPARSE on hosted macOS but pass on Linux? Original test and baseline must not be altered. No independent source-rewriting branch or duplicate Reader implementation.

## Mechanism / prediction
The original fixture writes 4096 A bytes, seeks to 16MiB-4096, writes 4096 B bytes. In parent source, Builder.scan calls codec._sparse_data_extents, which requires >=1 MiB, SEEK_DATA and SEEK_HOLE availability, st_blocks*512 < .75*size, and reported data extent bytes < .75*size. Predict hosted macOS fails one gate or gets different extents, Linux passes; direct scan / final archive storage must reveal this. Falsifier: both hosts pass the exact extent gates and scan as S_SPARSE but only final archive storage changes, or unchanged parent test failure cannot be reproduced.

## Stronger controls / disproof
Install exact parent CMPCT and measure three files with same deterministic logical SHA and length: (A) original seek-and-write, (B) ftruncate plus pwrite, (C) fully materialized zero bytes plus same A/B edges. For each, independently capture st_size, st_blocks, SEEK_DATA/SEEK_HOLE outcomes and errors, codec sparse-detection output, genuine Builder.scan storage, final built archive Reader storage, reader.verify, extraction SHA. All controls must have equal logical bytes. Run Ubuntu 24.04 and macOS 14; retain every negative as raw result. Rerun original unchanged nine-test parent suite as separate exit-status control; do not suppress Mac red.

## Alternatives, boundaries and decision
Host sparse accounting, APFS extent reporting, unsupported SEEK_DATA/SEEK_HOLE, and Builder postscan rewriting are plausible alternatives. If the actual attribution is ambiguous, mark it ambiguous, not a successful repair. One hosted two-OS cheap diagnostic is sufficient to tell whether owner needs a truly portable direct sparse storage fixture vs a real encoder bug. Never change benchmark/format/release law or docs/discovery/STATE.json (owned by PR #440). Source evidence is research only; no product, CI release, or speed credit.

## Concurrency and handoff
Separate scientific surface; #472/#479 own product composition and original parent test. Preserve prereg chronology before adding instrument. Send result-bearing exact-head run and limiting negative to owners, without weakening inherited assertions.

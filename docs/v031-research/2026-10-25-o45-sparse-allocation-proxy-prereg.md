# O45 — Sparse allocation proxy versus canonical r24 storage selection (preregistration)

**Date:** 2026-10-25 UTC. **Status:** prospective research-only; no product, format, frozen-workload or release authority.

## Exact custody and primary question

Is the revision-24 Builder's `st_blocks*512 >= 0.75 * logical_size` prefilter a sound proxy for the `SEEK_DATA/SEEK_HOLE` sparse data topology, and can it cause the same logical source bytes/metadata to select different physical archive representations? The starting source is O42 PR #396 head `757577eed13bf277e003c4d3c694cc9e4f67d2c3`. Bind actual `src/cmpct/builder.py` blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, `src/cmpct/codec.py` blob `29526db4203723d83523fc95d074c346b63d7587`, and O42 semantic witness `65711cf8644f4eb1863499262ae8bfd787010d2e`. Any source drift must fail the experiment, not be silently accepted.

## Baseline and alternatives

Original Builder `_sparse_data_extents` first checks physical allocation size, then probes `SEEK_DATA/SEEK_HOLE`. Linux filesystems can record unwritten/preallocated extents in `st_blocks` while still reporting them as logical holes through `SEEK_DATA`. This is a *structural admission* question, not a compression-tuning exercise.

Strong simpler control: if baseline sparse versus filled allocation differs in logical bytes/metadata, archive difference is uninteresting. Keep one 8 MiB regular-file inode, one path, fixed `mtime_ns` and mode, exact same logical SHA-256, hardlink/xattr partition and O42 semantic witness; compare sequential snapshots. Restore the sparse state as a further no-drift control. Use source-exact `Builder` and `CMPCT`, not a simulated codec or substituted archive format.

## Prediction and falsifiers

Pre-register three structural conditions: (A) sparse file with a nonzero 4 KiB terminal extent; (B) same inode after `posix_fallocate(fd,0,size)`, which may charge all blocks while leaving `SEEK_DATA` unchanged because new extents are unwritten; (C) same inode after actually writing all logical zeros and restoring terminal data. Predict `st_blocks` A << B ~ C and `SEEK_DATA` A == B > 0, C == 0 **only on hosts exhibiting the unwritten-extent behavior**. Predict original Builder uses `S_SPARSE` for A and a different physical strategy for B. B may regress complete archive bytes and scanned/encoded work, but no byte-size win is presumed.

A positive decision requires: same inode/path/mode/mtime/content/xattrs/witness; independently observed `st_blocks`, `SEEK_DATA/SEEK_HOLE` and full exact Builder/Reader roundtrip; genuine r24 archives; actually changed representation for A vs B; measured full archive bytes; no source/format mutation. Both A and B strong `verify()` must pass. Control C discriminates preallocation from written dense extents. If the host does not exhibit the advertised extent behavior, report UNSUPPORTED_HOST rather than inventing a source/format loss. Any changed logical digest/mtime invalidates the claim.

## Opportunity cost / BONK

O42's official input witness already excludes physical sparse topology; do not change its official gate. The prior O43 local sparse control found an independent 4 MiB filesystem layout difference but **did not execute the real Builder**. This experiment is the cheapest missing causal discriminator: one authentic source-exact r24 Builder comparison, not a new codec, another ABBA matrix or a near-duplicate hardlink test. If difference is immaterial or Builder still selects the same representation, retire the family. If meaningful, hand off to Builder/evidence owner: first estimate full-system payoff versus the extra `SEEK_DATA` probe on every large file before proposing a product patch.

## Evidence / constraints

An isolated, non-frozen Linux hosted probe will publish JSON and logs, with repeat physical controls and independently rechecked derived claims. Costs recorded: complete bytes, copy/allocation state, resulting storage kind, snapshot logical size, naive sparse-probe opportunity, and limited build time (descriptive only). No timing or size release credit, no historical corpus mutation, no official comparator/threshold change. Benchmark truth stays frozen. Do not update discovery shared state while #240 owns it. Preserve negative outcomes and precise host constraints.

## Concurrency claim

Narrow owner surface: `tools/v031_o45_sparse_allocation_proxy.py`, `.github/workflows/v031-o45-sparse-allocation-proxy.yml`, and two O45 research notes. This is orthogonal to O42's official corpus witness implementation, O44 held-out hardlinks, and O38 hardlink product work. Source import from O42 is read-only. No duplicate scientific credit for the previously established abstract filesystem fact.

**Promotion:** none. **Disproof threshold:** any contradiction in the observed source-exact causal chain.

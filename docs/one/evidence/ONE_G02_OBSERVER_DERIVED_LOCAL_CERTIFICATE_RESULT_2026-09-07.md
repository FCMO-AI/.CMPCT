# ONE-G0.2 observer-derived local certificate result — 2026-09-07

## Decision

**REJECT the observer-derived 32-byte bottom-8 certificate shape and close ordinary local-certificate carrying-cost work in the current Gear observer.**

This is a mechanism-level negative. It does not invalidate the earlier structural observation that tiny local witnesses can recover useful shifted/fragmented relations; it demonstrates that maintaining such witnesses per byte in the present observer is far too expensive, even after eliminating the second rolling Gear recurrence and almost all eight-way target scans.

## Exact authority

- branch: `research/cmpct1`
- exact source: `b6048ad8254e8d97c75a2bcccefaebd4701c6a8a`
- workflow run: `34090037423`
- job: `101641474555`
- artifact: `10006614574`
- artifact zip SHA-256: `076dc808e0a6ecb8f77f31c1e4f9be0c9904f90714aa73eaeb3f1907e2be32cc`
- `tests/one`: **93 passed**
- strict native build (`-O3 -std=c11 -Wall -Wextra -Werror`): PASS
- workflow conclusion: failure because the frozen triage gate correctly rejected the candidate.

## Frozen aggregate result

Candidate / mandatory-observer baseline:

- mature median: **2.137240x** (gate <=1.15x)
- fragmented mature median: **2.173843x** (gate <=1.15x)
- mature worst: **2.211813x** (gate <=1.25x)
- tiny median: **2.129440x** (gate <=1.25x)

Per-row ratios:

| row | ratio | exact nomination | target threshold passes | target hash checks |
|---|---:|---:|---:|---:|
| tiny 4 KiB shift+1 | 2.109294x | 1 | 1 | 6 |
| tiny 8 KiB fragmented96 | 2.149587x | 1 | 1 | 1 |
| mature 64 KiB shift+1 | 2.211813x | 1 | 1 | 3 |
| mature 256 KiB fragmented96 | 2.173843x | 1 | 2 | 9 |
| mature 256 KiB independent random | 2.158022x | 0 | 9 | 72 |
| mature 1 MiB independent random | 2.116355x | 0 | 2 | 16 |
| mature 1 MiB already-compressed-like | 2.112477x | 0 | 6 | 48 |
| mature 1 MiB repeated/versioned | 2.116457x | 1 | 1 | 1 |

The independent direct-window oracle, native nomination decisions and mandatory observer counters agreed before timing. Independent-random and compressed-like controls produced zero exact false nominations.

## Causal interpretation

The opportunity gate worked. On the 1 MiB independent-random control, approximately 2.1 million source+target certificate windows were derived, yet only **2** target windows crossed the retained-max threshold and only **16** retained hashes were checked. The compressed-like control similarly required only 6 threshold passes / 48 checks. Therefore target-side eight-way search is no longer the dominant cost.

What remains is the per-byte derived-local-fingerprint machinery itself:

- a 32-entry delay-ring load/store;
- extraction of the delayed prefix state;
- a shift/subtract to derive the local 32-byte value;
- source-side bottom-8 maintenance during source observation;
- additional loop dependencies and state pressure inside an otherwise very cheap mandatory Gear observer.

Those costs approximately double the observer even when the target gate is almost never entered. This is direct evidence for the current Genesis speed rule: eliminating a second recurrence is insufficient if the replacement still adds serial per-byte state to a simple hot loop.

## Research decision

Do **not** attempt another local-certificate micro-redesign by changing K, 32-byte window size, ring layout, threshold, file-size dispatch, corpus dispatch, branch hints, or unrolling. Two independently preregistered native carrying shapes have now failed by large margins:

1. independent rolling certificate: mature median 3.358603x;
2. observer-derived certificate: mature median 2.137240x.

That is enough causal evidence to close ordinary work on this family during Genesis.

A local-certificate principle may be revisited only if a future mandatory bulk/vector observation primitive emits suitable local witness information as a near-free byproduct, or if a later end-to-end profile demonstrates that the recovered relation density is worth a separately justified compute budget. Do not bolt it onto the present per-byte observer.

## Claim boundary

No reader-visible mechanism changed. No ONE0 bytes, density, RSS, selective-access, release, v0.29/v0.30 or full-ingest superiority claim follows from this result.

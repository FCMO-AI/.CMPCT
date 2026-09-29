# Shifted post-PrefixGraph futility proof-point audit

Status: **FORGE R0 CAUSAL AUDIT / CURRENT-PROFILE SOURCE ORDER / NO PRODUCT OR RELEASE CREDIT**

Authority audited: `agent/v030-authoritative-integration@94f3309011ca6f6014b1f61ce6058e8ce01ca00f`.

Issue: #194.

## Question

The preserved post-PrefixGraph nomination oracle proves very large conditional headroom on Shifted: once the exact PrefixGraph winner exists, omitting the later losing G0-G4/v0.29 candidate removes about 31.28 s median complete-create wall while preserving exact bytes/tree/locality.

Can a deployable **exact futility proof** observe enough unavoidable bytes early enough in the current product to recover a material fraction of that headroom, or do current builders expose their first useful exact size facts only after the expensive search has already run?

## Current product execution boundary

The canonical r25 product executes the isolated PrefixGraph process first and waits for it to exit before entering the G0-G4 path. The current scheduler identifies this as:

`prefixgraph-process-level15-then-g04-main-v1`.

Therefore the completed PrefixGraph incumbent is available before G0-G4 starts. The surviving problem is not incumbent availability.

Current G0-G4 is owned by `entropygraph_v030_shared_portfolio`:

1. spawn exact v0.28 and attempt-5 pre-fallback graph workers;
2. wait for both exact candidate artifacts;
3. reconstruct the accepted v0.29 floor;
4. apply G0-G4 to the retained attempt-5 graph;
5. exact-price and publish.

On current Shifted evidence, the shared child build is roughly 43.6 s while the post-shared overlay is roughly 4.2 s. A proof that fires only after both graph artifacts exist cannot recover the large nomination-oracle opportunity; it can only remove the late overlay.

## Source-order audit

Current v0.28 `_build_graph` and attempt-4 Placement `_build_graph` both perform the following work independently:

- enumerate and read the same files;
- preflate eligibility/probes;
- FastCDC node construction and exact aliasing;
- similarity sketches;
- inherited LSH candidate discovery;
- direct-cost compression;
- inherited delta encoding plus payload compression;
- central-base assignment;
- v0.28 pack-plan pricing.

Placement then adds position-independent discovery, broad delta auditions, bounded multi-root mosaic subset search, placement/co-pack pricing and its own record/materialization work.

Attempt-5 `build_graph` does not replace this cost with an earlier proof surface: it first completes the full Placement graph, then runs the residual-pack compiler and chooses between the residual and Placement embodiments.

## Why the obvious exact physical-byte bound is late

Before inherited delta auditions complete, the final root/delta assignment is not fixed. Direct costs are not a sound lower bound on final graph bytes because exact delta/mosaic representations may replace them.

Before pack-plan pricing completes, root-pack physical payload costs are not fixed.

Before Placement's bounded mosaic/placement search completes, its transformed record set and exact savings are not fixed.

Therefore the simple proof grammar

`already-forced physical bytes + immutable framing > PrefixGraph incumbent`

does not currently become informative until after the dominant delta/mosaic/pack search that issue #194 needs to avoid. This is the same causal weakness preserved by the historical exact-LB-w3 negative, even though later implementations can remove duplicate probe compression.

The ML hostile remains binding: a tiny pre-overlay gap can become a large exact winner, so an empirical early byte-gap threshold is not a substitute.

## Decision

**Do not implement a late post-graph size check and call it productization of the 31 s oracle.**

Two materially different successor classes remain:

### A. Pre-search exact necessary condition

Derive a mechanically valid bound from facts available before broad graph search (input structure, already-completed PrefixGraph state, or a new exact invariant) that upper-bounds how much v0.28/Placement/Residual/G0-G4 can still improve.

This route survives only if it is sound on arbitrary content, fails open, preserves ML-like near-frontier winners, and fires before a material fraction of both spawned child walls.

### B. Shared execution architecture

If no nontrivial pre-search proof exists, stop the pruning family and attack duplicated execution directly. v0.28 and Placement currently recompute a large common analysis substrate independently. The next cheap instrument should measure ownership of the common stages (read/preflate, CDC, sketches, inherited LSH, inherited delta auditions, pack planning) versus Placement-only mosaic/residual work.

A product successor may then factor a single exact analysis IR and derive both candidates without changing either candidate's byte semantics. That requires byte-for-byte/current-tree controls and full RSS/process accounting.

## Next falsifier

Instrument current-profile Shifted plus at least one held-out structured transfer case and report, for each child:

- wall in shared common analysis;
- inherited delta-audition count/time;
- pack-plan time;
- Placement-only broad/mosaic search time;
- residual compiler time;
- final candidate bytes/tree identity.

If the common exact substrate is not a material owner, retire shared-analysis reuse. If it is, prefer R2 execution sharing over heuristic publishability prediction.

No release threshold, comparator, format, reader or admission law changes in this audit.

# CMPCT v0.31 — Disjoint Sparse Extent Magic Continuity O1

Date: 2026-10-23

**Status:** prospective independent hostile scientific replication. **NOT product integration or an authenticated recovery claim.** Exact parent: PR #296 head `6951d88518bc2cda8ab31af6577aac3ff4215b4c`; `benchmarks/v031_sparse_seek_salvage_court.py` blob `94fc2234df0035938be3151dfaa5eef7bc317598`; bounded incumbent `src/cmpct/transactions.py` blob `94c25029fdd167c00871aabbe8fe90fbe7490026`.

## Question and baseline

The parent O0 reported exact candidate parity for a set of sparse, dense and cross-hole layouts. Its oracle retains the last three scanned bytes (`carry`) as it iterates physical extents, then prepends those bytes when scanning the next extent. But `SEEK_DATA` can advance over a *logical zero-filled hole* between extents. Concatenating bytes from two nonadjacent extents is not equivalent to scanning the logical file. Moreover, the oracle's `BHDR.unpack` path does not re-check that the bytes read at the asserted logical offset begin with `CMA4`.

An exploratory local *reenactment* (not the committed original PR296 module, not prospective hosted evidence) placed `CMA` at the end of one allocated page, then `4` at the beginning of a later allocated page after a real sparse hole. It produced a phantom record at 8189, whose four on-disk bytes were `00 00 00 34`, while a full logical scan found none. This motivates a source-exact independent replication; it is not a claim against the hosted parent until the original module is executed.

## Frozen prediction

On Linux/FS supporting meaningful `SEEK_DATA`/`SEEK_HOLE`, construct an otherwise zero-filled file above the parent admission threshold with (A) an allocated page ending `CMA`; (B) a *different noncontiguous data extent* starting `4` followed by sufficient zero bytes; and (C) a full, independent, syntactically valid `BHDR` entirely within a third data extent as a positive control.

- The authentic bounded scanner should return only (C), because it scans logical bytes with the hole.
- The unchanged parent sparse oracle should report (C) **plus** a phantom candidate whose claimed logical `offset` is B_start-3, inside a hole and with on-disk magic different from `CMA4`.
- The *admitted* default sparse route should exhibit the same mismatch, since the source is physically sparse and exceeds 1 MiB.
- Repeating with A/B contiguous (no hole) should not be conflated with this defect: magic may legitimately span a continuous read boundary.
- A full header beginning in a data extent and continuing into a hole remains discoverable; resetting cross-extent carry must not disable that separately supported semantic.

The hosted court must establish the actual allocated-data extents before interpreting results. If the filesystem cannot expose a genuine intervening hole, report **UNSUPPORTED/NO DECISION**, not scientific PASS.

## Falsifiability and alternatives

**Kill the existing general 'exact candidate parity' scientific claim** if the hosted original oracle yields a phantom; this does *not* negate measured huge-sparse execution headroom. If parent oracle already handles the discontinuity, or the baseline also identifies the claimed offset as an actual logical `CMA4`, the hypothesis is falsified. If physical extent reports are incoherent or unsupported, the claim is unresolved. The strongest simpler control is the inherited `recover_blob_records` over the *same exact file*. No fixture-ID admission and no change to the original comparator or product.

Potential minimum fixes for the owner to evaluate *after evidence*:
1. reset `carry` when the next data extent starts after the prior logical `stop`;
2. independently check `header[:4] == BMAGIC` before considering any candidate;
3. ideally do both for defense-in-depth without changing the logical candidate contract.

Cost: at most a reset/constant check on sparse fast-path; no archive byte change. Non-concurrent source assumption persists. The scientific script is not yet product code. No material `docs/discovery/STATE.json` mutation.

## Counterfactual discriminator

A **two-extent, one-hole, split-magic** file is the cheapest known falsifier of extent-boundary continuity, distinctly sharper than a valid header whose tail spans a hole. This prospective commitment precedes the source-exact GitHub-hosted instrument and result.

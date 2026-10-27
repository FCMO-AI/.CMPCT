# O212 preregistration — same-effective-index sparse geometry admission

**Date (UTC):** 2026-10-27. **Status:** prospective hypothesis; written before any O212 product/test edit.

## Authority and ownership
Released v0.30.0 / revision-24, unmerged v0.31. Parent: O193 PR #521 exact `392112ce859db5a7f85be593c82d1cabc1f5131f`; Python Reader blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`; strict validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`. Science O198 #532, O202 #539, economics O205 #542, same-source limitation O208 #546. Issue #533 is the correctness owner; O193 owns the ZIP64 implementation. This child claims only **ordinary Python Reader S_SPARSE geometric admission**, not general Reader rearchitecture, ZIP64, or source immutability.

## Baseline and hard invariant
A root-versioned, correctly authenticated revision-24 index with an S_SPARSE extent declared shorter than the sum of referenced blob logical sizes currently passes ordinary Python `CMPCT(...)` and `verify()`, but returns zeros for `read_range(2,2)` while full `read()` yields `CD`. Existing strict `validation._validate_storage()` rejects the contradictory geometry; native Rust also rejects it. A successful normal Python Reader open must never expose incoherent sparse geometry that can make full/range/extract disagree.

## Primary question
Can the Reader admit the **already loaded effective index** using the same strict `_validate_storage` sparse geometry contract, once per open before mmap/read, without independent pathname reopen, reimplementation of the rule, or disturbing valid r24 archives?

## Falsifiable predicted outcomes
1. Valid root-versioned `S_SPARSE` [0,4,[blob0 of four bytes]] opens, verifies, full/range reads and extracts byte-exactly, including the genuine sparse 4GiB / 4096-extent use case.
2. Three root-versioned, same-physical-record hostile variants with declared lengths 1, 2 and 5 **raise at opening**. Failure occurs before any member read/verify and does not modify archive bytes.
3. Existing representation and recovery compatibility tests continue to pass. No ZIP64 change, new on-disk revision, parser threshold weakening or separate filesystem open.
4. New scoped validation does not materially increase small sparse open or high-extent open CPU/wall/RSS relative to the strongest preflight controls; measurement must separate no-op opens from full decompression and avoid tracemalloc timing skew.

## Strong simpler control and alternative explanation
A second pathname preflight was observed as ~17ms extra on one high-extent fixture (O205), but O208 proved its source identity may diverge between opens; this is **not** a valid safety substitute. A direct duplicated geometry loop is smaller but risks drift against the strong existing validator. Stronger alternative: validate `_validate_index` on the same in-memory index; investigate only if sparse-only integration demonstrably leaves a material unsupported grammar gap. An early `_validate_storage` exception must close its owning file descriptor, and a valid archive should open on existing supported platforms.

## Decision and kill conditions
Promote only after positive normal and adversarial native-source installed-package CI, exact-parent/HEAD identity, existing recovery and 4GiB sparse ZIP64 positive, bounded-memory/performance accounting and final release parity. Kill/narrow if strict call accepts any bad length; if an independently authored valid r24 archive is rejected; if source identity differs; if the added validation incurs unjustified carrying cost; or if concurrent owner changes invalidate the exact-parent code. A successful unit suite alone is *research/provisional*, not release proof.

## Concurrency and scope
O212 branch is a stacked child of O193 #521; no edits on the O193 parent branch. No other research instrument, historical benchmark, frozen comparator, format, threshold, CI guard, Discovery policy or canonical release may be modified. Preserve negatives. Re-read parent PR/issue before shared writes or any integration proposal.

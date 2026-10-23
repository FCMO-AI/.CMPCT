# CMPCT v0.31 independent two-process stale journal O1 — preregistration

**Status:** prediction frozen before implementation/results; Linux/fork research only. This is a distinct physical-process replication of the already-completed and source-exact single-process O0 (#289), not a new Writer implementation.

## Authority and scope
- Authentic Writer source blob: `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c` at development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- O0 source `eb5c28c24e52b763a4925787025c9dba21476bbf`, GitHub Actions run `40027031272` reproduced a silent lost update with separately threaded real calls, two successful returns, predecessor 927 referenced by both, and serialized complete physical generation writers. O0 is source-exact scientific negative, no product credit.
- Linux only; `multiprocessing.get_context('fork')` is explicit, not a Windows compatibility claim. No format, product source or release policy changes.

## Primary question / prediction
Do **two distinct OS processes**, each making a real public `transactions.append_rename` call on one archive, both return success while only one logical mutation survives when they snapshot the same footer and serialize each complete physical generation append across processes?

**Predicted:** sequential public baseline preserves both disjoint renames; controlled two-process run returns success from both, observes two complete noninterleaving appends with equal predecessor footer and distinct terminal footer offsets, latest `CMPCT.by` contains exactly one of the two new names and both file payloads remain readable. Final `verify()` passes for the one surviving logical generation.

## Strongest control, alternatives, falsifier
- Control sequential independent exact same input and operations; establish both are legal.
- Barrier after original `CMPCT.__exit__` in both OS processes, so each has finished its original read/validation/snapshot before either can append.
- Shared OS-process `multiprocessing.Lock` encloses **the unchanged entire `_append_generation` call**, excluding writes interleaving.
- Capture each independent process exit code, final statuses and footer predecessor/position via `multiprocessing.Queue`. A process failure, timeout, unreadable archive, wrong source SHA, or missing control classifies as a different failure / AMBIGUOUS, not the predicted *silent* loss.
- Hypothesis **FALSIFIED** if both operations succeed, whole appends are serialized, and both mutations survive. Distinct snapshots invalidate the scheduling precondition.
- Do not patch actual product data validation or footer semantics. Test-only scheduling is not a product feature.

## Decision relevance and scope limits
If confirmed, process-level independence removes an alternative explanation involving Python threads/GIL. Serializing the writer's low-level append is insufficient; meaningful ownership must encompass snapshot/validate/commit. This does *not* prove multiwriter use was promised; product semantics must be explicitly designed and cross-platform identity/locking/recovery verified. Source aliases, concurrent archive replacement, NFS and Windows remain outside this court. No Discovery Engine policy change from one case.

## Coordination and durable handoff
PR #289 is primary research owner; Issue #290 is confirmed capability/assumption boundary and includes Linux lock-inode vs namespace negative. Dormant `agent/phased1-v031-transaction-multiwriter-ownership` branch remained at development HEAD with no commits; do not overwrite it. Other Writer guards (#241/#245/#247/#250) remain owner-separated. Future promotion requires actual product repair and independent recovery/portability/performance CI.

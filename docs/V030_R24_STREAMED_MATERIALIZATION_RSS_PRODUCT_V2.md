# v0.30 r24 streamed materialization — controlling RSS product lane

Status: **ACTIVE RESEARCH BRANCH / NO RELEASE CREDIT**

## Why this lane is active again

Authoritative runtime run `35472257484`, artifact `10593415740`, closes all frozen timing gates after DGO1 productization but fails the frozen parent/self pack-RSS gate. Totals: median create `1.0442608x`, max create `1.2437836x`, median extract `0.9421727x`, max extract `1.1901246x`, max pack RSS `2.1345453x`.

The whole-process-tree companion reports RSS `1.0x`, but its own contract declares `release_credit=false`; it is diagnostic and cannot erase the frozen main-gate failure.

With the decisive historical pack peak at 122,992 KiB, the 1.25x ceiling is 153,740 KiB. Current candidate hurdles are:

- Shifted: 262,532 KiB; remove at least 108,792 KiB.
- Logs: 168,576 KiB; remove at least 14,836 KiB.
- ML: 203,300 KiB; remove at least 49,560 KiB.

PR #157 independently attributed roughly +115,200 KiB of Shifted incremental high-water to r24 Builder construction from the same prebuild baseline. That is large enough in principle to close the hardest frozen RSS hurdle, so r24 materialization is the primary causal target.

## Product mechanism

Current `Builder.build()` retains multiple complete generations simultaneously: raw candidates; the full retained encoded-result list; complete record bytes; joined `data`; and the final `header+index+data+index+footer` bytes passed to `write_bytes()`.

This branch restores the already-tested `ordered_worker_iter()` primitive on top of current authority. It bounds scheduled/completed encoding results while preserving canonical observation and failure ordering. It is not a product win until Builder actually consumes it incrementally.

The smallest shipping-shaped experiment is:

1. consume encoded results in canonical order through `ordered_worker_iter()`;
2. append each exact physical record to a disk-backed temporary spool;
3. retain only index scalars/hashes and release each candidate raw payload as soon as all later Builder logic no longer needs it;
4. after the index is known, stream header, compressed index, spooled records, duplicate index and footer directly to the destination;
5. preserve byte-for-byte archive identity, deterministic failure ordering, publication semantics and worker bound.

## Kill / promotion conditions

First measure r24-only Shifted against exact-parent construction. If the component experiment cannot recover roughly 109 MiB while preserving exact archive SHA/bytes, do not pay whole-product CI. Charge temp bytes/I/O and wall/CPU; a RAM-backed spool or a large timing regression is not a win. ML create has little max-gate margin on the fresh authority run (`1.24378x` versus `1.25x`), so memory cannot be bought by slowing the critical path.

Only unchanged whole-product frozen authority can award release credit. No threshold, corpus, comparator, timing boundary or RSS definition may move.

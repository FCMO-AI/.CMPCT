# v0.30 r24 streamed materialization — parked product optimization

Status: **DRAFT / NONBLOCKING / NO RELEASE CREDIT**

## Authority and baseline

The controlling authoritative whole-process-tree companion is run `35437119021`, artifact `10582612465`. It reports `max_peak_rss_ratio = 1.0`; therefore the frozen 1.25x RSS release gate is already **GREEN**. Parent/self-RSS ratios from the companion runtime are mechanism-localization signals only and may not override that authority.

PR #157 still found a real product-memory opportunity. From the same 123,324 KiB prebuild high-water, Shifted r24 construction added **115,200 KiB** while r25 added **23,024 KiB**. A later child-harness refinement showed that import/prebuild baselines themselves can mask component increments, so ML ownership was deliberately left unresolved rather than forced. PR #157 and the earlier import diagnostic #156 are closed as decision-complete provenance.

## Mechanism

Shipping `src/cmpct/builder.py::Builder.build()` currently retains several generations simultaneously:

1. `self.cands[*].raw` owns source/candidate bytes;
2. `ordered_worker_pull()` returns a complete list containing every compressed payload;
3. Builder constructs a second complete `records` list containing header+metadata+payload bytes;
4. `b''.join(records)` allocates complete `data`;
5. `out.write_bytes(header+ic+data+ic+footer)` allocates another complete archive-sized bytes object.

The archive order is deterministic: candidates are sorted by hash and ordered worker output preserves that order. The extra generations are implementation state, not format semantics.

## Product hypothesis

Consume encoded results in bounded canonical order. For each result, preserve only the scalar/hash/usize metadata required by the index, release the candidate's raw bytes, and write the complete encoded record to a disk-backed spool. Once the index is known, stream `header`, compressed index, spooled records, duplicate compressed index and footer directly to the destination. Do not construct complete encoded-result, `records`, joined-`data`, or final-archive byte generations in RAM.

The first primitive is implemented on this branch: `ordered_worker_iter()` limits scheduled/completed results to O(workers), preserves canonical observation order, and closes its claim gate immediately when an already-submitted worker fails. Dedicated tests cover reverse completion, bounded claims, latent later-worker failure and lowest-index exception observation. It is not wired into Builder yet, so it earns no RSS/product claim.

The completed implementation must preserve exact candidate order/codec competition, exact archive SHA/bytes, deterministic failure ordering, current worker bound, publication semantics, format/readers/selectors/thresholds/corpora/dependencies/public APIs. A temporary disk spool is acceptable only with complete temp-I/O and wall accounting; a memory spool that silently grows to archive size is not a win.

## Priority

This lane is parked behind controlling timing work: PR #155 (ML create) and PR #152 (extraction scoping) have higher current release leverage. Resume only when those lanes are independently blocked/pending or after timing gates close, unless later authoritative evidence makes RSS controlling again.

## Evidence ladder when resumed

1. Finish Builder wiring: ordered iterator + raw release + deterministic record spool + streamed final assembly.
2. Same-source A/B on frozen Shifted and ML r24-only construction: exact archive SHA/bytes; wall/CPU, peak RSS, temp bytes and I/O.
3. Run unchanged full concurrent product RSS/runtime authority; component peaks never earn release credit.
4. Retire/narrow if exact identity/failure semantics change or carrying cost exceeds measured whole-product value.

No frozen RSS threshold may move.

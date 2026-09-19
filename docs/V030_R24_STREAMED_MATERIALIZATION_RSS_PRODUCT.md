# v0.30 r24 streamed materialization — product preregistration

Status: **DRAFT / NO RELEASE CREDIT**

## Baseline

Unchanged authoritative runtime `35437105192` reports pack-RSS ratios of 2.1333x on Shifted and 1.6587x on ML against the frozen 1.25x ceiling. Import-only PR #156 ruled out module footprint as the primary owner.

PR #157 run `35450761900` measured r24-only versus r25-only construction, but a later baseline instrument found that the child process had imported the heavy corpus-builder harness before measuring product work. Run `35450870427` therefore narrows the trustworthy statement: from the same 123,324 KiB prebuild high-water, Shifted r24 added **115,200 KiB** while r25 added **23,024 KiB**. That is already enough to establish r24 Builder as the primary Shifted component. ML was partly masked by the harness high-water and must not be assigned from that run. Source `eacdb018…` removes the corpus-builder import from child mode; its clean run controls ML attribution.

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

The completed implementation must preserve:

- exact candidate order and codec competition;
- exact archive SHA/bytes on every control corpus;
- deterministic failure ordering and fail-closed claim behavior;
- current worker bound and no unbounded future/result queue;
- current atomic/product publication boundary;
- no format, reader, selector, threshold, corpus, dependency or public API change.

A temporary disk spool is acceptable only if complete temp-I/O bytes and wall cost are measured. A memory spool that silently grows to archive size is not a win.

## Cheapest decisive evidence ladder

1. Finish Builder wiring: ordered iterator + raw release + deterministic record spool + streamed final assembly.
2. Same-source A/B on frozen Shifted and ML r24-only construction: archive SHA/bytes must be identical; record wall/CPU, pack peak RSS, temp bytes and I/O.
3. Kill if Shifted peak does not fall enough to make the full-product 1.25x RSS ceiling credible, or if wall/temp-I/O cost materially erases product value.
4. Treat ML independently according to the clean PR #157 discriminator; do not extrapolate Shifted ownership.
5. If the component hurdle clears, run unchanged full concurrent r24/r25 product RSS/runtime authority. Component peaks do not earn release credit.

## Controls / alternatives

- Merely lowering worker count is weaker: it may reduce transient codec workspace but leaves the retained archive generations.
- Replacing exact codecs/levels is prohibited because it can alter bytes/selection.
- Serializing r24 and r25 exports create-wall cost and does not cure the measured isolated Shifted r24 working set.
- r25/G04 memory work remains a separate route if the clean ML discriminator assigns ML there.

## Disproof / retirement

Retire or narrow this route if exact archive identity changes, deterministic failure semantics cannot be preserved, temp-I/O/wall cost dominates the RSS gain, or a correctly measured implementation cannot materially reduce Shifted r24 RSS. Do not relax the frozen 1.25x RSS ceiling.

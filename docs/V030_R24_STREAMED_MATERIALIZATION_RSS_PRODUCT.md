# v0.30 r24 streamed materialization — product preregistration

Status: **DRAFT / NO RELEASE CREDIT**

## Baseline

Unchanged authoritative runtime `35437105192` reports pack-RSS ratios of 2.1333x on Shifted and 1.6587x on ML against the frozen 1.25x ceiling. Import-only PR #156 ruled out module footprint as the primary owner.

PR #157 component run `35450761900` / artifact `10587035475` isolates construction:

| workload | r24-only peak | r25-only peak | full v0.30 peak (authority) |
| --- | ---: | ---: | ---: |
| Shifted | 238,920 KiB | 160,220 KiB | 253,804–261,692 KiB |
| ML | 139,772 KiB | 121,224 KiB | 198,380–203,472 KiB |

All isolated archives strong-verified. r24 is therefore the largest measured isolated RSS component on both controlling workloads, and by itself nearly explains Shifted's complete high-water.

## Mechanism

Shipping `src/cmpct/builder.py::Builder.build()` currently retains several generations simultaneously:

1. `self.cands[*].raw` owns source/candidate bytes;
2. `ordered_worker_pull()` returns a complete list containing every compressed payload;
3. Builder constructs a second complete `records` list containing header+metadata+payload bytes;
4. `b''.join(records)` allocates complete `data`;
5. `out.write_bytes(header+ic+data+ic+footer)` allocates another complete archive-sized bytes object.

The archive order is already deterministic: candidates are sorted by hash and ordered worker output preserves that order. The extra generations are implementation state, not format semantics.

## Product hypothesis

Replace full-result retention with bounded ordered consumption and spool record bytes while building the deterministic blob table. After the index is known, write `header`, compressed index, spooled records, duplicate compressed index, and footer directly to the destination stream. Do not construct complete `records`, `data`, or final-archive byte strings in RAM.

The implementation must preserve:

- exact candidate order and codec competition;
- exact archive SHA/bytes on every control corpus;
- deterministic failure ordering equivalent to current `ordered_worker_pull`;
- current worker bound and no unbounded future/result queue;
- current atomic/product publication boundary (this change is inside Builder materialization only);
- no format, reader, selector, threshold, corpus, dependency or public API change.

A temporary disk spool is acceptable only if complete temp-I/O bytes and wall cost are measured. A memory spool that silently grows to archive size is not a win.

## Cheapest decisive evidence ladder

1. Implement bounded ordered iterator + record spool behind the existing Builder semantics.
2. Same-source A/B on frozen Shifted and ML r24-only construction: archive SHA/bytes must be identical; record wall/CPU, pack peak RSS, temp bytes and I/O.
3. Kill if Shifted peak does not fall enough to make the full-product 1.25x RSS ceiling credible, or if wall/temp-I/O cost is material enough to erase product value.
4. If the component hurdle clears, run unchanged full concurrent r24/r25 product RSS/runtime authority. Component peaks do not earn release credit.

## Controls / alternatives

- Merely lowering worker count is a weaker control: it may reduce transient compression workspace but leaves all four retained encoded generations.
- Replacing exact codecs/levels to save memory is prohibited because it can alter bytes/selection.
- Serializing r24 and r25 may reduce overlap but exports create-wall cost and does not cure r24's measured 238,920 KiB isolated Shifted peak.
- r25/G04 memory work is lower priority until this measured r24 owner is falsified or rehabilitated.

## Disproof / retirement

Retire or narrow this route if exact archive identity changes, deterministic failure semantics cannot be preserved, temp-I/O/wall cost dominates the RSS gain, or a correctly measured implementation cannot materially reduce the isolated r24 peaks. Do not relax the frozen 1.25x RSS ceiling.

# J24S02 — prospective zero-run CRC algebra, subordinate to J24S01

**2026-10-26; research only.** Inherited source is J24S01 PR #525 at `87f8ccd2acc6c3da41fb8c6bf09c6536e5ba1ff4`. Released CMPCT is v0.30.0/r24; this experiment neither changes the Reader nor claims a ZIP64 product gain. J24S01 already established exact DEFLATE fragment reuse and charged SHA256/CRC32 for known sparse holes. **This question is different**: can exact algebra remove the remaining *repeated CRC32 scan* for adjacent known-zero extents while preserving the SHA256 scan, stream identity, and all checks?

## Baseline, causal mechanism and alternatives

Current J24S01 `encode()` charges `zlib.crc32(data, crc)` on each logical hole span, alongside SHA-256. CRC-32 is a linear GF(2) remainder; `crc32_combine(crc_A, crc_B, length_B)` can advance a CRC state over a known block without rescanning its bytes. A zero run of length N has a CRC expressible by exponentiation/combination in O(log N) bitmatrix work. **Candidate:** merge adjacent structural zero-hole descriptors for CRC only, use CRC combine on the entire coalesced zero run; still update SHA256 over exactly every logical byte and keep the *identical* J24S01 DEFLATE operations, emitted bytes, full input file length and authentication comparisons.

Three controls must be kept separate: (A) the inherited incremental 1-MiB `zlib.crc32` on all bytes; (B) the cheaper ordinary approach, one `zlib.crc32` per contiguous zero run on a materialized bounded zero buffer, where feasible; (C) the algebraic O(log N) CRC run advance. A per-chunk algebraic advance is an additional overhead control; do not compare against intentionally poor Python loops only. No compression ratio credit: DEFLATE bytes must be byte-identical.

## Prospective falsifier

Evaluate 256-MiB all-hole, 256-MiB mixed with 4-KiB inserts each 16 MiB, and 64-MiB no-hole using same deterministic spans, levels 1 and 6, interleaved >=3 independent repetitions, explicit wall+CPU, peak RSS where measurable, and actual full CRC/SHA. Also check adversarial small/unaligned hole lengths, interleaved data, and nonzero starting CRC against independently executed `zlib.crc32` on materialized logical bytes.

**Continuation:** all exact tests pass; median *complete oracle encoder wall* improves >=5% on 256-MiB sparse zero and mixed at at least one level, with <=2% no-hole slowdown, no byte-size or format change, and no uncharged materialization/memory. If improvement fails or overhead dominates, retire as a full-product priority; do not tune thresholds based on the result. CPU-only CRC savings without wall or with higher memory are insufficient. Larger runs may only get an isolated research credit, not product credit.

## Scope / threats / handoff

Honor J24S01 source as the strong compression control; do not rewrite its instrumentation or replay/freeze criteria. Authentication of sparse zero extents depends on valid structural admission; malformed extent geometry, same-inode mutation, output-stage identity and hostile filesystem races remain separately owned. Algebra cannot avoid SHA256's linear cost, nor assert secure source immutability. Store original measurements and negative alternatives in a linked result note; no shared `STATE.json` writes or discovery policy rewrite unless decision-changing repeated evidence demands it. A hosted workflow may confirm local micro evidence, but library oracle != real archive benchmark.
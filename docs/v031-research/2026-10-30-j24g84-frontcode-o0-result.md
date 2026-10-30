# J24G84 O0 result — unconditional path frontcoding rejected; scoped seed preserved

Date: 2026-10-30 UTC. **RESEARCH O0, not product/release evidence.** Immutable prereg commit: `3721819520889b1994f8be5aaaa03747799568c6`. Source code blob: `71cf5ef26992833f56b2528a891860e25530547e`. Exact hosted source HEAD: `e50afd65c335487f3f5657163f4e054f8423aa0d`. GitHub Actions [41063037132](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063037132): **SUCCESS**. Original artifact [12982235329](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063037132/artifacts/12982235329); downloaded ZIP SHA-256 `1ca79ef0ccf6963c1904207d87213f681f76932bd47aa0b5924bed4fb6739a60`, identical to GitHub artifact digest. Host dependencies: `zstandard=0.25.0`, MessagePack version `1.2.4`. Actual Writer/Reader product source unchanged from v0.31 development base.

## Prospectively predeclared question and verdict
Hypothesis: unconditional byte-exact adjacent-name frontcoding of **complete** CMPCT index then Zstd-19 beats original complete MessagePack index under identical Zstd-19 in >=2/4 structural families by >=5% AND >=256 bytes, **without** >1% regression on any case. **Verdict: NO_GENERAL_METADATA_HEADROOM** because one structural hostile regresses 2.17%. Three material positive cases are scoped research seeds, not an unconditional family success. No threshold or comparator changed.

| Authentic Builder family | Original complete compressed index | Frontcoded complete compressed index | Δ bytes, B-A | % saved |
| --- | ---: | ---: | ---: | ---: |
| Flat numbered | 1,257 B | 464 B | -793 B | +63.09% |
| Deep directories | 4,221 B | 1,413 B | -2,808 B | +66.52% |
| Random/hash-like names | 65,921 B | 67,352 B | **+1,431 B** | **-2.17%** |
| Mixed Unicode | 8,708 B | 3,476 B | -5,232 B | +60.08% |

These are **complete compressed index payloads**, not complete archive-size deltas. Full actual archives generated solely for baseline provenance measured 3,134 B flat; 9,916 B deep; 154,628 B random; 23,720 B Unicode, but the alternative is an oracle representation and no valid CMPCT alternate-format archive was materialized. Hence **zero product byte credit**. The same original index's MessagePack bytes and all other metadata were included on both sides. Original and reconstructed MessagePack SHA-256 match byte-for-byte in all four classes. There were 10 wall+CPU observations per representation per family. The detached no-CMPCT auditor recalculated all sizes, medians, decision and negative controls. Eight semantic-name list controls covered empty, duplicated, shuffled, Unicode combining/noncombining and surrogateescape names; malformed framing was rejected.

### Mechanism and counterevidence
The positive cases indicate Zstd-19 does **not** automatically recover all adjacency redundancy embedded in MessagePack row interleaving. Explicit prefix/suffix facts can reduce index entropy significantly, but in names with high-entropy hash-like siblings they add prefix/framing/cross-field noise that defeats even the *uncompressed* frontcoded-size improvement: original 166,280 B MsgPack vs frontcoded 164,038 B, yet compressed 65,921 B vs 67,352 B. Thus **uncompressed size is an insufficient admission predictor**. All four results remain visible; no hidden conditional success assertion.

### External mature control and novelty claim
RocksDB/LevelDB block encodings already use shared-prefix length, nonshared suffix, and restart points. This test does **not** claim invention of front coding. RocksDB's current block table implementation also exposes optional common-prefix optimization with explicit read/seek CPU tradeoffs: https://github.com/facebook/rocksdb/blob/main/include/rocksdb/table.h . The CMPCT-specific question is whether a fully charged adjacent path stream can beat an already strongly compressed authenticated *complete filesystem index*, not whether prefix compression is new.

### Whole-system debit ledger / strongest self-critique
- No total wire archive alternative, reader integration, format selector, full parse/verify/recovery, cold read/ZIP/native parity, cross-platform RSS or create/extract throughput was measured.
- 2,048 real files per family were chosen to give the name scheme generous headroom; content dedup/reproducible metadata may exaggerate its contribution to whole archive size.
- The prototype has sequential name reconstruction/dependency across all previous names. Random member lookup may incur amplification; restarting/sparse offset indexing would add bytes/complexity.
- The strict 1% hostile veto fired. Do **not** publish unconditional frontcoding or call it generic improvement.
- Host timings are warm in-process library research only; not historical product or frozen benchmark measurements.

### Next cheapest decision
Test a bounded, **charged encoder-only** prefix admission policy, rather than unconditional frontcoding, against the exact original Zstd-19 control. A low-level Zstd-1 dual-probe of complete original and candidate indexes may predict which Zstd-19 representation wins, with no stored additional bytes when the original remains selected. Must charge both probes, creation of candidate index, format-tag byte when candidate selected, and selector/decode complexity; false admission creates stored-byte regression and falsifies usefulness. Before any new implementation preregister a new question and prospective decision criterion. Alternatively retire the positive seed if the admission overhead erases wall/CPU gains. No state update; PR #574 owns discovery cache.

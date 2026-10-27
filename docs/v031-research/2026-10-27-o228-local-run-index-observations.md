# O228 — local charged virtual-reference-run oracle observations (NOT product evidence)

**Date:** 2026-10-27 UTC. **Evidence class:** independent local, synthetic r24-**shaped** MessagePack/Zstd12 index science; **not a valid serialized CMPCT archive or Reader measurement**. Preregistered at `cdcf643d37dfda2d6d212ce794c6683b27dd46d9` before either instrument/result. Shipped `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains unchanged.

## Local source/results custody

Full local script SHA-256 `eba82188be269188bf067e92af5c7e74e89c490daf681d57ab388754d6888bff`; original raw JSON SHA-256 `71b942f75950e2e07949e9d7fecf7db097de72d5fa442381ea857cc4bf43e40e`. The durable GitHub instrument `research/o228_virtual_reference_run_oracle.py` and separately rooted `research/o228_independent_audit.py` independently reconstruct the same scientific question but are **not byte-identical** to the local instrument. Do not silently relabel these local receipts as hosted/exact-head GitHub evidence. The hosted [O228 workflow](https://github.com/FCMO-AI/.CMPCT/actions/workflows/v031-o228-virtual-reference-run.yml) carries original audit artifacts and must decide its **own** HEAD.

Local 14 profiles × two variants × 3 separate interpreter processes = **84** observations. All local full logical `(length, owner)` sequence SHA-256 fingerprints matched, 27 sampled selected-byte hashes matched per profile, and 11 malicious run-count/owner/length/declared-size controls were rejected per profile. These are semantics of the **research grammar**, not official CMPCT conformance.

## Raw-synthetic index bytes and unpack heap medians

Full top-level index encoded with MessagePack, compressed with libzstd level 12; both physical owner tables and member logical SHA are present. The table shows *one* primary-index size in bytes; a real dual-index accounting duplicates it. `heap` is `tracemalloc` heap peak **during MessagePack unpack only**, not process RSS or total decoder memory. Provisional local observations:

| Kind | Shape | Runs / refs | Explicit index B | Run index B | Explicit unpack heap MiB | Run unpack heap MiB |
|---|---|---:|---:|---:|---:|---:|
| fixed | all same | 1 / 262144 | 186 | 167 | 2.00 | <0.01 |
| fixed | run128 | 2048 / 262144 | 3265 | 345 | 2.01 | 0.18 |
| fixed | run8 | 32768 / 262144 | 371 | 466 | 2.01 | 2.76 |
| fixed | run2 | 131072 / 262144 | 418 | 505 | 2.01 | 11.01 |
| fixed | alternating | 262144 / 262144 | 204 | 276 | 2.00 | 22.00 |
| fixed | random32 | 253902 / 262144 | 165204 | 227190 | 2.00 | 21.31 |
| fixed | unique32k | 32768 / 32768 | 110609 | 68538 | 5.37 | 7.87 |
| CDC | all same | 1 / 262144 | 241 | 167 | 20.00 | <0.01 |
| CDC | run128 | 2048 / 262144 | 7314 | 436 | 20.01 | 0.18 |
| CDC | run8 | 32768 / 262144 | 503 | 493 | 20.01 | 2.76 |
| CDC | run2 | 131072 / 262144 | 501 | 531 | 20.01 | 11.01 |
| CDC | alternating | 262144 / 262144 | 252 | 276 | 20.00 | 22.00 |
| CDC | random32 | 253902 / 262144 | 232917 | 250891 | 20.00 | 21.31 |
| CDC | unique32k | 32768 / 32768 | 143297 | 69980 | 7.62 | 7.87 |

## Decision and strongest counterexample

**Preliminary result: `CONDITIONAL_VIRTUAL_INDEX_HEADROOM`**, not universally promotable. The run128 **CDC** case reduced index bytes 7314→436 (94.0%) and MessagePack unpack heap ~20.01→0.18 MiB (about 112x), while preserving the full logical sequence. For fixed run128 index bytes fell 3265→345 (89.4%) and unpack heap ~2.01→0.18 MiB (11.25x). These reductions alone do not establish full Reader or Builder savings.

**Counterexample:** fixed run8 actually **increased** compressed index bytes 371→466 and unpack heap 2.01→2.76 MiB. Alternating and random owners were considerably worse in compressed bytes and heap. Despite strong single-run results, an unconditional run format is dominated in these classes by the simpler explicit representation. For unique32k, compressed run bytes happen to be smaller but the heap is larger; this mixed vector cannot be counted as overall dominance.

The prospective cheap discriminator was not 'repetition exists', but **full compressed index economics**: Zstd can represent rapid repeated low-cardinality literals more compactly than a run grammar that carries explicit count/length/owner triples. A byte-protective portfolio needs a complete-index comparison, or a rigorously proven bound; mere local run length is not a sound admission rule. A fully encoded dual-index comparison still incurs *both* encoder passes. Better writer-side admission/streaming proof and changed representation/reader bounds remain unmeasured.

## Self-critique / next gates

The local case families do not establish that the shipping Builder actually selects S_CHUNKS/CDC for these source patterns (sparse detection or more economical representations may win); the physical-record totals were only common cost proxies; no Builder-created authentic archive, HEAD source-equivalence, journal, recovery, adversarial index-signature, native/Windows/macOS or actual cold-open/full-read parity evidence exists. Python heap `tracemalloc` excludes allocator/RSS context. The long repeated-run case is an optimistic workload, not a benchmark-wide prevalence claim.

Next: evaluate outcome from hosted [PR #600](https://github.com/FCMO-AI/.CMPCT/pull/600) exact-head oracle artifacts without assuming results; if confirmed, research a **bounded generic hybrid** whose exact preserved facts permit virtual range access and whose chooser can reject high-diversity cases before material compression cost. Do not collide with #569 product Reader or #574 discovery state, change existing format revision 24, adjust version, or merge this PR on research data.

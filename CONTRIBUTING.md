# Contributing to CMPCT

CMPCT is currently an internal FCMO-AI research project.

For every format-affecting change:

1. state the workload/problem being solved;
2. add or update a regression test;
3. benchmark at least one adversarial workload where the idea could lose;
4. document any new on-disk field, codec, transform or invariant;
5. preserve byte-exact round trips;
6. preserve intentional design footnotes in the reference code;
7. avoid Hermes-specific heuristics unless they are expressed as generic measurable policies;
8. never trade recovery, safety or random access away merely for a prettier compression ratio;
9. distinguish encoder-only heuristics from reader-required format semantics;
10. record compatibility consequences before merging;
11. update `docs/HISTORY.md` and `docs/CURRENT_STATE.md` when the version/frontier changes;
12. commit benchmark evidence under `benchmarks/history/` for material size/speed decisions;
13. preserve losing results and rejected ideas when they materially influenced design, normally in `docs/RESEARCH_LOG.md`.

`main` is the canonical source of truth. Pre-1.0 changes may break old archives only when the format
revision changes and the incompatibility is documented.

## Required benchmark provenance

Do not submit a performance claim as a naked number. Record, as far as practical, the source commit,
format revision, corpus generator/hash/seed, environment, codec settings, timing semantics,
metadata/integrity/durability semantics, repetitions and the raw or summary measurements.

Historical results are append-only evidence. Do not alter old benchmark records merely because a
new implementation produces different numbers.

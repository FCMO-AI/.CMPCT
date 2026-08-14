# Contributing to CMPCT

CMPCT is currently a pre-1.0 research and engineering project. Public/open-source licensing is being
considered but is **not yet finalized**; see `LICENSING.md`.

For every format-affecting change:

1. state the workload/problem being solved;
2. add or update a regression test;
3. benchmark at least one adversarial workload where the idea could lose;
4. document any new on-disk field, codec, transform or invariant;
5. preserve byte-exact round trips;
6. preserve intentional design footnotes in the reference code;
7. avoid corpus-specific heuristics unless they are expressed as generic measurable policies;
8. never trade recovery, safety or random access away merely for a prettier compression ratio;
9. distinguish encoder-only heuristics from reader-required format semantics;
10. record compatibility consequences before merging;
11. update `docs/HISTORY.md` and `docs/CURRENT_STATE.md` when the version/frontier changes;
12. commit public benchmark evidence under `benchmarks/history/` for material size/speed decisions;
13. preserve losing results and rejected ideas when they materially influenced design, normally in `docs/RESEARCH_LOG.md`;
14. comply with `docs/PUBLIC_SURFACE.md`: do not import private customer/project data, unrelated internal system context, private corpus identities, personal information, private artifact names, credentials, or private-system URLs into the public-facing project tree.

`main` is the canonical source of truth. Pre-1.0 changes may break old archives only when the format
revision changes and the incompatibility is documented.

## Required benchmark provenance

Do not submit a performance claim as a naked number. Record, as far as practical, the source commit,
format revision, corpus generator/hash/seed, environment, codec settings, timing semantics,
metadata/integrity/durability semantics, repetitions and the raw or summary measurements.

Private development corpora may be useful internally, but public benchmark claims should be based on
reproducible public or synthetic inputs. Historical public results are append-only evidence; do not
alter them merely because a new implementation produces different numbers.

## Licensing while the proposal is non-final

The repository currently carries an **Apache-2.0 proposal**, not a finalized grant. Do not add source
headers that state the project is Apache-2.0 licensed unless the licensing proposal has been formally
adopted and `LICENSING.md` has been updated accordingly. Third-party code must keep its existing
license and attribution requirements regardless of the project's eventual license.

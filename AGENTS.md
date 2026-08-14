# Agent instructions

This repository is the canonical CMPCT project.

## Required orientation before development

Before changing format behavior or encoder policy, read:

1. `README.md`;
2. `docs/CURRENT_STATE.md`;
3. `docs/HARDENING.md`;
4. `docs/PORTABILITY.md`;
5. `docs/FORMAT.md`;
6. `docs/HISTORY.md`;
7. `docs/RESEARCH_LOG.md`;
8. `docs/BENCHMARKS.md`;
9. `docs/ROADMAP.md`.

Do not depend on inaccessible chat history for project-critical context. If a new conclusion matters to future work, put it in the repository.

## Development rules

- Optimize for arbitrary computer files and filesystems, not Hermes specifically.
- Hermes is one regression corpus only.
- Do not delete design footnotes/comments from code when rewriting or refactoring.
- Every code fix should include concise nearby commentary explaining why the fix exists when the invariant is non-obvious.
- Never claim a benchmark win without equivalent semantics and a reproducible test.
- Prefer adding a losing/adversarial corpus over tuning a threshold to one successful corpus.
- Keep the reader contract simpler than encoder heuristics: old archives must remain readable after encoder strategy changes once 1.0 is frozen.
- Treat malformed archives as hostile input. Bounds, path and resource-limit checks are mandatory.
- For parser/conformance work, keep `docs/HARDENING.md` current so unfinished safety assumptions do not disappear into chat or one-off tests.
- Treat a fair, reproducible ZIP win as an engineering gap to investigate; never hide it by changing timing boundaries, workloads, or semantics.
- Keep library-to-library and CLI/process-start benchmark layers separate so startup overhead cannot masquerade as codec/format performance.
- Portability is a release gate: keep `docs/PORTABILITY.md` current and design platform integrations around one shared memory-safe archive-handler core rather than independent parsers.
- Preserve fallback behavior when optional native helpers/codecs are absent.
- Update `docs/FORMAT.md` in the same change as any on-disk format mutation.
- Update `docs/HISTORY.md` and `docs/CURRENT_STATE.md` whenever a version/revision materially changes project behavior or the development frontier.
- Durable benchmark results belong under `benchmarks/history/`; do not leave the evidence only in terminal output, chat, or prose.
- Preserve historical benchmark files; append new records instead of rewriting old results to match a new narrative.
- Distinguish measured fact, inference, planned work and rejected experiment explicitly in documentation.

## Benchmark rule

Any change justified by size/speed should commit or reference a durable benchmark record containing, when available: source commit, format revision, corpus generator/hash/seed, environment, codec settings, cache/process-start semantics, metadata/integrity/durability semantics, repetitions and raw/summary measurements.

## Versioning rule

A new on-disk field/record/storage semantic required by readers normally requires a format revision bump. Encoder-only heuristic changes that still emit the same grammar do not, but they still require regression evidence and history/current-state updates when material.

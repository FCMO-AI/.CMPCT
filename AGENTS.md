# Agent instructions

This repository is the canonical CMPCT project.

## Required orientation before development

Before changing format behavior or encoder policy, read:

1. `README.md`;
2. `docs/CURRENT_STATE.md`;
3. `docs/HARDENING.md`;
4. `docs/PORTABILITY.md`;
5. `docs/NATIVE_CORE.md` when native/portability work is in scope;
6. `docs/FORMAT.md`;
7. `docs/HISTORY.md`;
8. `docs/RESEARCH_LOG.md`;
9. `docs/BENCHMARKS.md`;
10. `docs/PUBLIC_SURFACE.md`;
11. `docs/ROADMAP.md`.

Do not depend on inaccessible chat history, private corpora, unrelated internal projects, or private
artifact provenance for project-critical context. If a conclusion matters to future CMPCT work, put
the generalized technical conclusion in this repository without importing unrelated confidential
context.

## Development rules

- Optimize for arbitrary computer files and filesystems, not any one development corpus.
- Private/internal corpora may be used locally for regression work, but their identity, contents and artifact names are not part of the public project contract.
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
- Keep `docs/NATIVE_CORE.md` current when the shared native ABI gains a representation, safety boundary, or portability-relevant capability.
- Preserve fallback behavior when optional native helpers/codecs are absent.
- Update `docs/FORMAT.md` in the same change as any on-disk format mutation.
- Update `docs/HISTORY.md` and `docs/CURRENT_STATE.md` whenever a version/revision materially changes project behavior or the development frontier.
- Durable public benchmark results belong under `benchmarks/history/`; do not leave public evidence only in terminal output, chat, or prose.
- Preserve public historical benchmark files; append new records instead of rewriting old results to match a new narrative.
- Distinguish measured fact, inference, planned work and rejected experiment explicitly in documentation.
- Keep the public repository/site free of unrelated internal project names, personal information, private URLs, credentials, customer data, private corpus identifiers and private artifact names. Follow `docs/PUBLIC_SURFACE.md`.
- Do not describe the proposed Apache-2.0 license as adopted until the checklist in `LICENSING.md` is completed and the canonical license file is deliberately finalized.

## Benchmark rule

Any change justified by size/speed should commit or reference a durable public benchmark record
containing, when available: source commit, format revision, corpus generator/hash/seed, environment,
codec settings, cache/process-start semantics, metadata/integrity/durability semantics, repetitions
and raw/summary measurements.

Private-corpus measurements may guide engineering internally, but public claims must be reproducible
without access to private data.

## Versioning rule

A new on-disk field/record/storage semantic required by readers normally requires a format revision
bump. Encoder-only heuristic changes that still emit the same grammar do not, but they still require
regression evidence and history/current-state updates when material.

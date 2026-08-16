# Agent instructions

This repository is the canonical CMPCT project.

## Required orientation before development

Before changing format behavior, encoder policy, performance, portability or the public site, read:

1. `README.md`;
2. `docs/CURRENT_STATE.md`;
3. the newest applicable note under `docs/releases/`;
4. `docs/PERFORMANCE_RELEASE_GATE.md`;
5. `docs/HARDENING.md`;
6. `docs/PORTABILITY.md`;
7. `docs/NATIVE_CORE.md` when native/portability work is in scope;
8. `docs/FORMAT.md`;
9. `docs/HISTORY.md`;
10. `docs/RESEARCH_LOG.md` and `docs/ENTROPYGRAPH.md`;
11. `docs/BENCHMARKS.md`;
12. `docs/PUBLIC_SURFACE.md`;
13. `docs/ROADMAP.md`.

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
- Treat a fair, reproducible competitor win as an engineering gap to investigate; never hide it by changing timing boundaries, workloads, or semantics.
- Keep library-to-library and CLI/process-start benchmark layers separate so startup overhead cannot masquerade as codec/format performance.
- Portability is a release gate: keep `docs/PORTABILITY.md` current and design platform integrations around one shared memory-safe archive-handler core rather than independent parsers.
- Keep `docs/NATIVE_CORE.md` current when the shared native ABI gains a representation, safety boundary, or portability-relevant capability.
- Preserve fallback behavior when optional native helpers/codecs are absent.
- Update `docs/FORMAT.md` in the same change as any on-disk format mutation.
- Update `docs/CURRENT_STATE.md` whenever a material milestone changes the canonical implementation, performance policy or research frontier.
- Update `docs/HISTORY.md` when format lineage, a durable architectural decision, or a superseded design checkpoint needs historical explanation.
- Every material CMPCT milestone must advance the project version and add `docs/releases/vX.Y.Z.md` in the same change. Do not leave substantive work represented only by a commit hash, chat, branch name, benchmark artifact, or PR number.
- Every material CMPCT version must run the release performance gate and commit a fresh public benchmark record for that version under `benchmarks/history/` before merge.
- A base-vs-candidate release comparison must use the exact same corpus tree and benchmark semantics. Never regenerate separate random corpora and call their archive-size difference a regression or improvement.
- Deterministic CMPCT archive-size regression on the release parity corpus has **zero-byte tolerance**. If the candidate emits larger archives for the same input, fix it or deliberately redesign the benchmark contract before release; do not loosen the gate to make the PR green.
- Confirmed create/extract slowdown outside the same-runner timing noise envelope blocks release. If the signal is ambiguous, improve measurement quality rather than declaring a win or regression from noise.
- Durable public benchmark results belong under `benchmarks/history/`; do not leave public evidence only in terminal output, CI artifacts, chat, or prose.
- Preserve public historical benchmark files; append new records instead of rewriting old results to match a new narrative.
- The website's large performance claims must be derived from committed benchmark records. Do not hand-copy headline percentages into HTML/JavaScript.
- Keep research-frontier results clearly separated from canonical reader/writer claims. Aggressive presentation is encouraged; compatibility fiction is not.
- Distinguish measured fact, inference, planned work and rejected experiment explicitly in documentation.
- Keep the public repository/site free of unrelated internal project names, personal information, private URLs, credentials, customer data, private corpus identifiers and private artifact names. Follow `docs/PUBLIC_SURFACE.md`.
- Do not describe the proposed Apache-2.0 license as adopted until the checklist in `LICENSING.md` is completed and the canonical license file is deliberately finalized.

## Benchmark rule

Any material project version must commit a durable public benchmark record containing, when available:
source commit, project version, format revision, corpus generator/fingerprint/seed, direct comparison
base, environment, codec settings, cache/process-start semantics, metadata/integrity/durability
semantics, repetitions and raw/summary measurements.

Private-corpus measurements may guide engineering internally, but public claims must be reproducible
without access to private data. Aggregate wins never authorize deleting a losing workload.

## Performance-release rule

`.github/workflows/zip-parity.yml` is a release gate, not optional telemetry. Its direct comparison is
owned by the candidate harness: it generates one corpus, freezes its metadata, fingerprints it, and
runs both the base and candidate CMPCT engines against that identical tree on one runner.

The gate currently applies two different statistical rules because the measurements have different
physics:

- **Archive size:** deterministic for identical input/encoder semantics, therefore **0 B regression**.
- **Timing:** repeated median on the same runner; fail only when slowdown clears both the documented
  relative and absolute noise thresholds. A future controlled benchmark environment may tighten that
  envelope, but may not silently remove the performance requirement.

See `docs/PERFORMANCE_RELEASE_GATE.md` for the full contract.

## Versioning rule

CMPCT has two independent version axes:

1. **Project version (`MAJOR.MINOR.PATCH`)** — advances for every material merged milestone: engine work,
   encoder policy, benchmark/research frontier, portability/integration capability, hardening, website,
   release tooling, or other substantive project behavior. The new version must be recorded in
   `pyproject.toml`, `docs/releases/vX.Y.Z.md`, and a matching public benchmark history record.
2. **On-disk format revision** — advances only when a reader must understand a new field, record,
   storage description, codec semantic, or reconstruction rule to open newly written canonical archives.

Therefore an encoder-only, research, site or release-engineering milestone can advance the project
version while the canonical format revision stays unchanged. Conversely, every format-revision bump is
necessarily a material project-version bump and must update `docs/FORMAT.md`, conformance vectors,
`docs/CURRENT_STATE.md`, and the durable history/benchmark material appropriate to the change.

There is no “minor enough to hide” exception for material work. If it changes what CMPCT can do, how
it behaves, what it proves, how it is presented, or the development frontier in a way worth merging,
give it a version and benchmark that version.

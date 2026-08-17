# Agent instructions

This repository is the canonical CMPCT project.

## Required orientation before development

Before changing format behavior, encoder policy, performance, portability or the public site, read:

1. `docs/AGI_ENGINEERING_STANDARD.md` — mandatory quality ratchet, invention protocol, evidence hierarchy and completion standard;
2. `README.md`;
3. `docs/CURRENT_STATE.md`;
4. the newest applicable note under `docs/releases/`;
5. `docs/PERFORMANCE_RELEASE_GATE.md`;
6. `docs/BREAKTHROUGH_REHABILITATION.md` — how to preserve a miracle-grade research gain while paying any regression debt before promotion;
7. `docs/HARDENING.md`;
8. `docs/PORTABILITY.md`;
9. `docs/NATIVE_CORE.md` when native/portability work is in scope;
10. `docs/FORMAT.md`;
11. `docs/HISTORY.md`;
12. `docs/RESEARCH_LOG.md` and `docs/ENTROPYGRAPH.md`;
13. `docs/BENCHMARKS.md`;
14. `docs/PUBLIC_SURFACE.md`;
15. `docs/ROADMAP.md`.

Do not depend on inaccessible chat history, private corpora, unrelated internal projects, or private
artifact provenance for project-critical context. If a conclusion matters to future CMPCT work, put
the generalized technical conclusion in this repository without importing unrelated confidential
context.

## AGI-grade engineering is the default, not a special mode

`docs/AGI_ENGINEERING_STANDARD.md` is normative for every material task.

“AGI-grade” is a quality standard, not a capability claim. It means that future work must combine
strong systems reasoning, explicit hypotheses, adversarial self-review, independent evidence and
measurable improvement with the same seriousness as the best work already merged into CMPCT.

Every **promoted material milestone** must apply the quality ratchet: preserve all verified strengths of
the inherited released state while improving at least one meaningful dimension or producing a durable
negative result that prevents wasted future work. Green tests alone are not sufficient evidence of
excellent engineering.

Exploration is intentionally less timid than promotion. A reproducible mechanism-level breakthrough may
temporarily regress another benchmark without being thrown away. In that case the agent must preserve
the seed, expose the regression debt, and continue engineering until the breakthrough survives while
the inherited release floor is restored. `docs/BREAKTHROUGH_REHABILITATION.md` is the normative protocol.
No-regression remains the promotion boundary, not a ban on high-upside experiments.

For non-trivial work, agents are expected to:

- establish the baseline and invariant before editing;
- identify the actual dominant cost or failure mechanism;
- consider multiple solution classes rather than reflexively implementing the first conventional fix;
- use primary literature, standards and mature implementations when outside evidence can materially
  change the design;
- prefer mechanism-level and Pareto improvements over corpus-specific threshold tuning;
- define a practical disproof test for the core hypothesis;
- attack the strongest surviving assumption with an adversarial test;
- preserve losses and ambiguous evidence rather than narrating them away;
- leave the repository with enough context that a new agent can understand not only *what* changed,
  but *why the mechanism should be trusted*.

When a problem appears impossible under the current framing, change the model of the problem before
lowering the standard of proof. “Engineering miracle” means discovering a better representation,
invariant or cost model that makes a previously difficult tradeoff tractable—not adding complexity for
spectacle. If such a miracle initially exports cost into another benchmark, do not reflexively tune the
miracle away; preserve it and attack the exported cost as the next engineering mission.

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
- **Do not consume a numeric project version for presentation/process work.** Website polish, documentation cleanup, repository presentation, workflow ergonomics and similar non-format work use the root `SURFACE_REVISION` track (`x.x.a`, `x.x.b`, …).
- A numeric CMPCT core release is reserved for a **material improvement to CMPCT itself**: archive/engine capability, compression or speed, reliability, recovery, portability/interoperability, or another product-level behavior that materially advances the format. Cosmetic, handoff-only, research-note-only or repository-niceness changes do not qualify.
- After the historical v0.27.1 checkpoint, normal numeric core advancement moves the `MAJOR.MINOR` line and uses `PATCH=0` for packaging compatibility. Do not create patch-number churn for small work.
- Every numeric core release must add `docs/releases/vX.Y.0.md`, run the release performance gate, and commit a fresh public benchmark record for that release under `benchmarks/history/` before merge.
- A coherent surface milestone advances `SURFACE_REVISION` once, not once per commit. Multiple commits that collectively form the same presentation milestone may share the same surface revision.
- A base-vs-candidate core-release comparison must use the exact same corpus tree and benchmark semantics. Never regenerate separate random corpora and call their archive-size difference a regression or improvement.
- Deterministic CMPCT archive-size regression on the release parity corpus has **zero-byte tolerance at promotion**. If a release candidate emits larger archives for the same input, it is not promotable yet; do not loosen the gate. A dramatic research breakthrough with such debt may be preserved and rehabilitated under `docs/BREAKTHROUGH_REHABILITATION.md` instead of being reflexively discarded.
- Confirmed create/extract slowdown outside the same-runner timing noise envelope blocks core-release promotion. If the signal is ambiguous, improve measurement quality rather than declaring a win or regression from noise. If a miracle-grade research seed creates a confirmed timing debt, preserve the measurement and repair it before promotion.
- Durable public benchmark results belong under `benchmarks/history/`; do not leave public evidence only in terminal output, CI artifacts, chat, or prose.
- Preserve public historical benchmark files; append new records instead of rewriting old results to match a new narrative.
- The website's large performance claims must be derived from committed benchmark records. Do not hand-copy headline percentages into HTML/JavaScript.
- Keep research-frontier results clearly separated from canonical reader/writer claims. Aggressive presentation is encouraged; compatibility fiction is not.
- Distinguish measured fact, inference, planned work and rejected experiment explicitly in documentation.
- Keep the public repository/site free of unrelated internal project names, personal information, private URLs, credentials, customer data, private corpus identifiers and private artifact names. Follow `docs/PUBLIC_SURFACE.md`.
- Do not describe the proposed Apache-2.0 license as adopted until the checklist in `LICENSING.md` is completed and the canonical license file is deliberately finalized.
- Treat complexity as a cost. A clever design that cannot be bounded, explained, independently tested or ported is not an acceptable miracle.
- Do not merely patch the reported example when the failure mechanism can be generalized into an invariant or property test.
- When a mature competitor wins fairly, preserve the loss, explain the mechanism if known, and turn an actionable weakness into a prioritized engineering target.
- For substantial representation work, account for archive bytes, creation/extraction cost, peak memory, selective-read bytes/decoded work, dependency depth, integrity/recovery work and portability burden. Do not optimize one scalar by silently exporting cost elsewhere.
- A breakthrough seed that improves one strategic metric dramatically while regressing another must open explicit regression debt. First attempt adaptive portfolio/fallback selection, then isolate exported cost, then change representation boundaries or invent a counter-mechanism. Do not optimize the breakthrough back out merely to make an intermediate matrix green.
- Before completion, perform the adversarial self-review and completion dossier defined in `docs/AGI_ENGINEERING_STANDARD.md`.

## Benchmark rule

Any numeric core release must commit a durable public benchmark record containing, when available:
source commit, project version, format revision, corpus generator/fingerprint/seed, direct comparison
base, environment, codec settings, cache/process-start semantics, metadata/integrity/durability
semantics, repetitions and raw/summary measurements.

Private-corpus measurements may guide engineering internally, but public claims must be reproducible
without access to private data. Aggregate wins never authorize deleting a losing workload.

Surface revisions do not create synthetic benchmark records merely to prove that HTML, CSS, docs or
repository presentation changed. They may still run ordinary tests and the site build gate.

## Performance-release rule

`.github/workflows/zip-parity.yml` is a core-release promotion gate, not optional telemetry. Its direct comparison is
owned by the candidate harness: it generates one corpus, freezes its metadata, fingerprints it, and
runs both the base and candidate CMPCT engines against that identical tree on one runner.

The gate currently applies two different statistical rules because the measurements have different
physics:

- **Archive size:** deterministic for identical input/encoder semantics, therefore **0 B regression at promotion**.
- **Timing:** repeated median on the same runner; fail promotion only when slowdown clears both the documented
  relative and absolute noise thresholds. A future controlled benchmark environment may tighten that
  envelope, but may not silently remove the performance requirement.

A failed gate does not erase a verified high-upside research result. For a breakthrough seed it creates
regression debt: preserve the seed and full evidence, rehabilitate the damaged metric, and rerun the
full gate. Promotion happens only after the debt is closed while the breakthrough gain remains.

See `docs/PERFORMANCE_RELEASE_GATE.md` and `docs/BREAKTHROUGH_REHABILITATION.md` for the full contract.

## Material-PR evidence dossier

Every material PR should make the following explicit in its body or linked durable records:

- **Problem/baseline:** the exact defect or opportunity and the inherited behavior;
- **Insight/hypothesis:** the mechanism expected to improve it and the invariant preserved;
- **Alternatives:** meaningful solution classes considered and why rejected paths lost;
- **Evidence:** tests, independent oracles, benchmark records and raw/durable result locations;
- **Losses/ambiguity:** workloads, platforms or metrics that remain worse, unchanged or inconclusive;
- **Breakthrough debt when applicable:** the preserved gain, every regressed metric, rehabilitation hypotheses, gain-retention test and promotion exit condition;
- **Safety/compatibility:** hostile inputs, resource limits, recovery, path semantics, format/ABI impact;
- **Performance:** size, latency, memory/selective-work consequences where relevant;
- **Future leverage:** the highest-value new capability or unresolved defect exposed by the work.

The repository PR template mirrors this structure. Do not fill it with generic prose; use concrete
claims that a reviewer can falsify.

## Versioning rule

CMPCT now has three distinct axes. Do not collapse them into one counter:

1. **Core project version (`MAJOR.MINOR.PATCH`)** — the numeric release identity used by packaging and
   durable benchmark records. It advances only when CMPCT itself receives a material format/engine
   improvement: better capability, performance, reliability, recovery, portability/interoperability or
   similarly meaningful product behavior. Under the prospective scarce-version policy, normal releases
   advance `MAJOR.MINOR` and use `PATCH=0`. Historical versions such as v0.27.1 remain immutable evidence
   of the older policy; do not rewrite them.
2. **Surface revision (`MAJOR.MINOR.LETTER`)** — presentation/process identity stored in
   `SURFACE_REVISION`, for example `0.27.a`. Site animation, copy/design, documentation cleanup,
   repository presentation and workflow/process ergonomics belong here. A surface revision never changes
   `pyproject.toml` merely to make the repository look nicer, and it does not require a fake benchmark
   record. One coherent surface milestone gets one letter even if implementation spans several commits.
3. **On-disk format revision** — advances only when a reader must understand a new field, record,
   storage description, codec semantic, or reconstruction rule to open newly written canonical archives.

A core release may leave the on-disk format revision unchanged when the material gain comes from encoder
policy, performance, reliability or interoperability that preserves reader grammar. Conversely, every
on-disk format-revision bump is necessarily a core release and must update `docs/FORMAT.md`, conformance
vectors, `docs/CURRENT_STATE.md`, and the durable history/benchmark material appropriate to the change.

The numeric version is a **claim of product progress**, not a commit counter. Do not bump it to reward
activity. If work improves only the public surface, use `x.x.a`. If work is useful engineering but not yet
a material core milestone, it may land without inventing a release number and should remain clearly
represented in code/tests/research history until it earns promotion.

Footnote: `tools/check_version_discipline.py` enforces the separation. It rejects numeric bumps without
archive/engine participation, requires benchmark/release evidence for a core release, validates the
alphabetic surface line, and prevents surface work from masquerading as a new core version.

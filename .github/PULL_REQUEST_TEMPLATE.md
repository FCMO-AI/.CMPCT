# CMPCT material-change evidence dossier

<!-- Read docs/AGI_ENGINEERING_STANDARD.md and docs/BREAKTHROUGH_REHABILITATION.md before completing a material PR. -->

## Problem and baseline

- **Observed defect/opportunity:**
- **Baseline on direct base:**
- **Invariant(s) that must survive:**
- **Dominant cost/failure mechanism:**

## Insight and hypothesis

- **Mechanism:** Why should this change improve the system?
- **Disproof test:** What practical result would show that explanation is wrong?
- **Quality-ratchet movement:** Which verified dimension becomes better, and which important dimensions must be restored before promotion?

## Alternatives considered

1. **Alternative:** — rejected/retained because:
2. **Alternative:** — rejected/retained because:
3. **Alternative:** — rejected/retained because:

## Evidence

- **Correctness tests / properties:**
- **Independent oracle / second implementation / standard agreement:**
- **Durable benchmark record:**
- **Raw/diagnostic evidence:**
- **Direct-base performance gate:**

## Losses, ambiguity and negative evidence

- Workloads/metrics that became worse:
- Results that are statistically or semantically ambiguous:
- Known cases where a competitor still wins:
- Rejected experiment(s) worth preserving for future agents:

## Breakthrough regression debt, when applicable

<!-- A miracle-grade seed may be preserved with debt, but it is not release-ready. -->

- **Breakthrough metric:** baseline → seed, absolute/relative gain:
- **Regressed metric(s):** baseline → seed, absolute/relative loss:
- **Scope:** workloads / operations / platforms affected:
- **Suspected exported cost:**
- **Rehabilitation hypotheses:** portfolio/fallback, cost isolation, representation redesign, counter-invention:
- **Gain-retention test:**
- **Promotion exit condition:**
- **Debt status:** open / closed / N/A

## Safety, integrity and resource accounting

- Hostile/malformed input considered:
- Peak memory / decoded bytes / I/O or materialization bounds:
- Integrity/authentication boundary:
- Recovery/crash-consistency consequence:
- Path/link/filesystem-semantics consequence:

## Compatibility and portability

- Project version:
- Canonical format revision changed? **yes/no** — if yes, link byte/schema + conformance updates:
- Reader / writer / native ABI impact:
- Optional dependency / fallback impact:
- Platform-specific assumptions or tests:

## Performance accounting

- Archive bytes:
- Create latency / CPU:
- Extract latency / CPU:
- Open/list/read latency:
- Selective-read bytes touched / bytes decoded:
- Peak memory:
- Dependency depth / reconstruction fan-out:

## Public-surface check

- [ ] No unrelated private/internal names, private corpus identifiers, credentials, customer data or private artifact provenance entered the public tree.
- [ ] Public performance claims are derived from durable benchmark evidence rather than hand-copied headline numbers.

## Completion gates

- [ ] I attacked the strongest surviving assumption with a practical adversarial/disproof test.
- [ ] I preserved existing design footnotes/comments unless their rationale was demonstrably obsolete and retained elsewhere.
- [ ] Non-obvious fixes/invariants have concise nearby “why” comments.
- [ ] A fair competitor loss was not hidden by weakening semantics, deleting workloads or moving timing boundaries.
- [ ] If this began as a breakthrough seed with regression debt, the original large gain still survives and every promotion-blocking debt item is closed.
- [ ] Material work advances the core version/release note/history only when promoted as a numeric core release.
- [ ] Deterministic archive-size parity/improvement and same-runner timing requirements passed without weakening the release gate before release promotion.
- [ ] The repository state alone contains enough evidence/context for a skeptical new contributor to understand why this work should be trusted.

## Future leverage

- **What this unlocks:**
- **Highest-value unresolved defect exposed by this work:**

# J24I04 — exact-source full-matrix A/A hosted result (2026-10-29 UTC)

**Disposition: `AA_FALSE_RED_REPRODUCED`; scientific/evaluator evidence only; release gate unchanged and not waived.**

## Authority, preregistration, and immutable identities

- Research PR: [#715](https://github.com/FCMO-AI/.CMPCT/pull/715), OPEN/DRAFT. Pre-result preregistration: `19babf93938af73d86f2e1b2806115efddc4dbf0`; implementation: `25feadb58b087dae401fcb9776f42c63e360c0c1`.
- Hosted full court: [run 40790465600](https://github.com/FCMO-AI/.CMPCT/actions/runs/40790465600), research job `123178186011`, SUCCESS at 2026-10-29T00:14:49Z. The GitHub job SUCCESS means the research court and its independent referee ran; **the unmodified product release checker returned nonzero (FAIL)** by experimental design.
- Evidence archive: [artifact 12862735561](https://github.com/FCMO-AI/.CMPCT/actions/runs/40790465600/artifacts/12862735561), 34,351,431 B. Downloaded ZIP SHA-256: `6ecee2cf88ebbecb0763a8f28b8b659be9631dabcbe2dc0006b71ea44cdfcc5a`.
- Harness head `f8229e7521c40c302387309add23b15b29e9a66c`. **A and B both execute historical #704 source `293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef`**, in distinct Git worktrees; both source maps and native payload hash agree. Independently rehashed retained native .so: 1,752,712 B, SHA-256 `f60f0b0a5d4874044124dc215e556f76522ef0cca9a2da94cdeccef96085dacf`.
- Corpus unchanged before/after: 7,713 files, 303,738,466 logical B, tree SHA-256 `b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f`. Ubuntu 24.04.5, Python 3.11.17. Exact unchanged canonical benchmark (eight families, library/CLI, two archive formats, create/extract, seven repetitions per sweep), four full sweeps in A/B/B/A order.
- Two actual retained full binary-library CMPCT archives were independently rehashed and matched: 16,793,303 B each, SHA-256 `624aeb1e92f676a969dfc819fefc28b6969423ebb923f7c2d67378b1ec7d58d2`. The other archive hashes are source-reported evidence, not independently rehashed physical bytes.

## Raw observed result — unchanged release checker flags two impossible causal source regressions

| Original release cell | A same source | B same source | Apparent delta | Result |
| --- | ---: | ---: | ---: | --- |
| binary/library/create | 115.620443 ms | 124.117412 ms | **+8.496969 ms / +7.3490%** | FALSE RED |
| combined/library/create | 287.574880 ms | 304.891847 ms | **+17.316967 ms / +6.0217%** | FALSE RED |

The original checker says **FAIL, 2 confirmed regressions** under its unchanged >5% AND >3 ms rule. Since source and native binary are identical on A and B, these cells **cannot establish a source change caused that performance difference**. This falsifies source attribution from one full-matrix gate result, not the validity of the strict product release guard itself.

The ABBA per-sweep medians isolate nonlinear temporal variation:

- binary A0/B1/B2/A3: **112.399 / 136.352 / 111.883 / 118.842 ms**. The first adjacent transition was +23.952956 ms, the last +6.959018 ms.
- combined A0/B1/B2/A3: **281.828 / 322.306 / 287.478 / 293.322 ms**. First transition +40.478281 ms, last +5.844347 ms.
- With two medians on each side, the reported difference equals `[(B1-A0)-(A3-B2)]/2`. A uniform linear time trend cancels, but the observed unequal transitions do not. The B1 sweep is anomalous in these two cells. The specific host-level cause is **not proven**; do not assert CPU throttling, cache, or a single external process without tracing.

## Separately executed external audit

A third, local Python/stdlib-only audit directly read the downloaded GitHub artifact, without importing the CMPCT referee, Builder, Reader, or official benchmark. It independently:

1. Rehashed the downloaded ZIP, native .so and two complete retained CMPCT archives; corroborated source-provenance claims against source maps and retained record, while expressly not claiming a bytewise independent audit of every historical source tree.
2. Recomputed **128 aggregate timing medians across all 64 matrix cells** directly from the four underlying sweep JSON files and matched the signed aggregate values.
3. Checked **32 archive-size cells**, identical source/native maps, same corpus fingerprint, four successful sweeps, seven repetitions each, original A/B/B/A order, original checker FAIL, two precisely matching false-red cells, and the exact adjacent-transition identity. There were **zero discrepancies**.
4. Independently identified **zero ZIP control false reds**, preserving the meaningful limitation that noisy conditions affected a subset of CMPCT create cells rather than all measurements uniformly.

The hosted independent referee also checked 64 cells and rejected seven deliberate forged-receipt classes. External audit uses a differently implemented recomputation, but inherits the *same underlying experimental host*; **this is not an independent hardware replication**.

## Decision / release guard / weakest assumption

**Scientific result: `AA_FALSE_RED_REPRODUCED`.** The current full-matrix evaluator can report a false product regression on identical source under actual hosted execution. The observed signal in the original #704 A/B runs (+22.82% and +17.79% binary-library-create) remains a genuine **release veto pending further causal adjudication**. An A/A false red does **not** retrospectively prove those historical A/B reds are noise and cannot grant a release waiver. This result concerns measurement attribution, not compression, creation throughput, memory, format, exactness, security or portability improvements to the product.

**Counterfactual / transferable lesson:** a source-identical full-matrix A/A court at the outset of #704 attribution would have prospectively shown that a strict release red can occur with unchanged code, before several weaker isolated B-only probes. The insight is reusable as *causal debugging method*, not a unilateral policy change: when source differences cannot explain a large timed cell, test a genuine same-source full-gate control before editing the Builder or weakening thresholds.

**Next executable decision:** notify #704 and existing source/benchmark attribution owner #238; preserve both old A/B reds and this A/A false red; require bounded same-source/environment-identical replication with direct host/load evidence before attributing the performance difference to Reader constructor changes. Do not commission another near-duplicate full matrix without a new decisive discriminator. Allocate new development to already-claimed extraction/ZIP safety/integrity convergence, rather than continuing this saturated attribution family.

## No-go boundaries

No product code, archive format, direct release evaluator, frozen corpus, thresholds, historical benchmark evidence or version was modified to produce this result. No merge or release authority is claimed. This evidence must remain linked to its exact source/harness SHA and raw artifact; do not let `docs/discovery/STATE.json` override it merely because a cache entry is newer.

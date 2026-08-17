# CMPCT website

This directory is the source for the CMPCT project website.

## Product role

The site is the human/agent front door for CMPCT, with one priority explicit: **the public experience is
performance-first**. The first screen should create impact, the second should prove the claim, and the
rest should earn trust through transparent engineering detail.

The site exposes:

- current core project/version/format state plus the non-semantic surface revision;
- the strongest committed research-frontier benchmark, clearly labeled when it is not canonical;
- current matched structural cross-format comparisons;
- a fresh exact-tree per-category frontier against solid Zstandard;
- direct-base release deltas as separate causal evidence;
- the latest canonical ZIP execution-parity evidence with archive-size/create/extract timing;
- workload-level wins and losses;
- core-release trajectory and breakthrough-rehabilitation release philosophy;
- Browser Lab creation and fixed-header inspection;
- machine-readable orientation for agents.

## Visual behavior

The visual system is intentionally dramatic while remaining technical rather than decorative:

- near-black technical canvas with high-contrast ivory text;
- hot orange as the primary project signal and acid green only for verified wins/gates;
- oversized benchmark typography and dense data hierarchy;
- animated hero depth, scan, orbit and particle fields with pointer-responsive parallax;
- staged hero entrance, scroll reveals, benchmark-value pulses and restrained card elevation;
- an animated information-graph diagram built from native HTML/CSS/SVG rather than decorative media;
- responsive layouts and full `prefers-reduced-motion` support;
- no externally hosted fonts, trackers, image dependencies, or design-source provenance.

The motion layer lives in `assets/motion.css` and `assets/motion.js`. It is additive: benchmark data,
navigation, Browser Lab and accessibility-critical behavior must remain functional if that layer never
runs.

The interface is allowed to feel ambitious. It is not allowed to invent numbers.

## Core version vs surface revision

Numeric project versions are reserved for material CMPCT archive/engine improvements. A nicer website,
clearer documentation, repository presentation, workflow polish or other non-format work does not
consume a numeric release number.

Those changes use the root `SURFACE_REVISION` file, with the form `x.x.a`, `x.x.b`, and so on. The
surface line follows the current project major/minor line. This category-evidence/policy milestone is on
the **0.29 surface line** while the core remains **0.29.0** and the canonical on-disk format remains
revision **24**.

`site/enhance_site.py` applies the presentation layer after the canonical data build. This separation is
intentional: visual work should not gain accidental authority over benchmark normalization or archive
semantics.

## Performance-content contract

`site/build_site.py` reads committed benchmark history and generates a normalized public performance
model. The homepage must never hand-copy a headline percentage that can drift away from the benchmark
record.

The current model distinguishes four questions:

1. **Whole-suite structural research position / arena** — current research-engine measurements against external archive tools on a matched aggregate tree. ZIP/Deflate is the familiar adoption headline; solid Zstd-19 is elevated beside it as the serious size comparator, even when CMPCT loses.
2. **Per-category storage frontier** — current CMPCT versus solid tar+Zstd-19 on each exact individual workload tree, with ZIP/Deflate measured on that same live tree as secondary context. This powers the workload tiles.
3. **Canonical ZIP execution parity** — `benchmarks/zip_parity_bench.py` records for the executable reader/writer, with separate library and fresh-process CLI archive-size/create/extract measurements. This powers the spreadsheet-like table lower on the page.
4. **Direct-base release delta** — candidate-vs-inherited-engine evidence used to decide whether a research release moved its own frontier forward. This remains release causality and must never overwrite the competitive category view.

Footnote: all four views are deliberately separate. Whole-suite aggregation can exploit different
context/deduplication opportunities than a sum of independently-created workload archives, so those
numbers are not interchangeable. Likewise, solid tar+Zstd is a serious **size** baseline with different
random-access/recovery semantics, not fictional feature parity. The lower ZIP table asks an operational
execution question, not a second storage-frontier question.

The category record is accepted only when it covers every current workload and declares that CMPCT,
ZIP/Deflate-9 and solid tar+Zstd-19 were measured during the same generated-tree lifetime. Some valid
synthetic office/media producers can embed run-varying metadata, so a later regeneration is not treated
as byte-identical merely because it came from the same generator. Row-local tree hashes preserve the
actual category provenance.

Core release candidates are benchmarked candidate-vs-base by `.github/workflows/zip-parity.yml` and the
research-specific workflows. Deterministic archive-size regression has zero tolerance **at promotion**.
A verified mechanism-level breakthrough may remain explicit research with regression debt while the
project preserves its gain and rehabilitates the damaged metric; it does not become the released
baseline until applicable debt is closed. See `docs/BREAKTHROUGH_REHABILITATION.md`. Timing regressions
use the same-runner relative+absolute noise envelope. Surface-only revisions do not manufacture core
release records.

## Public-surface boundary

The website must be buildable entirely from publishable CMPCT repository state. It must not expose
private customer data, unrelated internal projects, private corpus identity, private artifact names,
private URLs, personal information, credentials or chat history. `tools/check_public_surface.py` is a
CI tripwire for this rule; `docs/PUBLIC_SURFACE.md` is the normative policy.

Browser Lab conversion and fixed-header inspection are local operations. Selected user files are not
uploaded by the static site.

## Automatic canonical data

`build_site.py` generates:

- `project-data.json` — project state, normalized frontier evidence, canonical parity records and release history;
- `agent.json` — machine-readable orientation and non-negotiable core-release rules;
- `llms.txt` — compact agent/human orientation;
- build-time version/revision/commit markers in the page itself.

`enhance_site.py` then adds:

- the optional motion stylesheet and motion controller;
- `surface-revision.txt`;
- surface revision labeling in the page and machine-readable project state;
- schema-specific v0.28/v0.29 evidence adapters;
- distinct public copy for the structural arena, Zstd category matrix and canonical ZIP execution table;
- the machine-readable rule that no-regression is a release-promotion boundary rather than an exploration ban;
- the public explanation that site/repository polish does not consume a numeric core version.

Every validation build derives current CMPCT facts from repository state rather than copied marketing
numbers.

## Browser writer safety boundary

`assets/cmpct-browser-writer.js` emits a real revision-24 CMPCT subset for regular files. It intentionally
does not implement the full encoder policy or an independent browser reader. The canonical project
prefers a future WASM build of the shared native core over proliferating parsers. CI therefore creates
a browser-written archive and opens/reads it with the canonical Python reader.

The writer is hard-gated to the format revision it was reviewed against. A format bump must update and
re-test the writer; the website must never keep creating stale bytes under a new version label.

## Build locally

```bash
python tools/check_public_surface.py
python site/build_site.py --out _site
python site/enhance_site.py _site
node --check site/src/assets/app.js
node --check site/src/assets/motion.js
node --check site/src/assets/frontier-v029.js
python -m http.server 8000 -d _site
```

## Publication

`.github/workflows/pages.yml` validates pull requests. Canonical `main` publishes through GitHub Pages
after disclosure, site-data, surface-revision, JavaScript and Browser Lab compatibility gates pass.

Footnote: presentation changes are intentionally kept downstream of canonical evidence generation. A
future redesign may replace the motion language completely without changing archive bytes, benchmark
truth, the core project version, or the on-disk format revision.

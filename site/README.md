# CMPCT website

This directory is the source for the CMPCT project website.

## Product role

The site is the human/agent front door for CMPCT, but v0.26 makes one priority explicit: **the public
experience is performance-first**. The first screen should create impact, the second should prove the
claim, and the rest should earn trust through transparent engineering detail.

The site exposes:

- current project/version/format state;
- the strongest committed research-frontier benchmark, clearly labeled when it is not canonical;
- the latest canonical ZIP-parity evidence;
- workload-level wins and losses;
- release/version trajectory;
- the no-regression release policy;
- Browser Lab creation and fixed-header inspection;
- machine-readable orientation for agents.

## Visual behavior

The v0.26 visual system is intentionally more dramatic than the original editorial prototype while
remaining technical rather than decorative:

- near-black technical canvas with high-contrast ivory text;
- hot orange as the primary project signal and acid green only for verified wins/gates;
- oversized benchmark typography and dense data hierarchy;
- subtle grid/ruler/graph motion that communicates system structure;
- an animated information-graph diagram built from native HTML/CSS/SVG rather than decorative media;
- responsive layouts and `prefers-reduced-motion` support;
- no externally hosted fonts, trackers, image dependencies, or design-source provenance.

The interface is allowed to feel ambitious. It is not allowed to invent numbers.

## Performance-content contract

`site/build_site.py` reads committed benchmark history and generates a normalized public performance
model. The homepage must never hand-copy a headline percentage that can drift away from the benchmark
record.

The current model distinguishes:

1. **Canonical parity** — records emitted by `benchmarks/zip_parity_bench.py` for the executable reader/writer.
2. **Research frontier** — broader EntropyGraph evidence that may lead the canonical format but is explicitly labeled as research until promoted through the format/conformance/native stack.

Every material CMPCT update is benchmarked candidate-vs-base by `.github/workflows/zip-parity.yml`.
Deterministic archive-size regression has zero tolerance. Timing regressions are evaluated on the same
runner with repeated medians and a small relative+absolute noise envelope so shared-runner jitter does
not become a false product regression.

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
- `agent.json` — machine-readable orientation and non-negotiable release rules;
- `llms.txt` — compact agent/human orientation;
- build-time version/revision/commit markers in the page itself.

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
node --check site/src/assets/app.js
python -m http.server 8000 -d _site
```

## Publication

`.github/workflows/pages.yml` validates pull requests. Canonical `main` publishes through GitHub Pages
after disclosure, site-data, JavaScript and Browser Lab compatibility gates pass.

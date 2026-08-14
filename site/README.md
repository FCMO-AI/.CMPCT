# CMPCT website

This directory is the source for the CMPCT project website.

## Product role

The site is the human/agent front door for CMPCT: project explanation, current engine model,
quick-start documentation, durable benchmark viewing, machine-readable agent orientation, a fixed-
header inspector, and a conservative browser-side archive writer.

The site deliberately lives in `site/` rather than `docs/` so normative format documentation stays
plain, reviewable repository material instead of becoming coupled to a website framework.

## Visual behavior

The site implements a restrained project visual system directly, without publishing unrelated private
design-source material:

- charcoal/white structure dominates; orange `#FD5204` is reserved for actions, crossings and state changes;
- grid, boundaries, alignment and negative space carry the composition;
- the caret acts as an operator/cursor that enters a system instead of as decorative wallpaper;
- motion is brief and mechanical;
- no gradients, neon, particle fields or faux terminal/data-stream spectacle;
- monospace appears only for actual commands/data, while the rest of the interface stays sober and editorial.

## Public-surface boundary

The website must be buildable entirely from publishable CMPCT repository state. It must not expose
private customer data, unrelated internal projects, private corpus identity, private artifact names,
private URLs, personal information, credentials or chat history. `tools/check_public_surface.py` is a
CI tripwire for this rule; `docs/PUBLIC_SURFACE.md` is the normative policy.

Browser Lab conversion and fixed-header inspection are local operations. Selected user files are not
uploaded by the static site.

## Automatic canonical data

`build_site.py` reads the repository at build time and generates:

- `project-data.json` — project/version/format state plus durable public ZIP-parity benchmark records;
- `agent.json` — machine-readable orientation and reading order;
- `llms.txt` — compact agent/human orientation;
- build-time version/revision markers in the page itself.

Every validation build derives current CMPCT version/revision/benchmark facts from canonical source
files rather than manually copied marketing numbers.

## Browser writer safety boundary

`assets/cmpct-browser-writer.js` emits a real revision-24 CMPCT subset for regular files:

- direct RAW or raw-DEFLATE blobs;
- SHA-256 identity and CRC32 checks;
- exact-content deduplication;
- revision-24 MessagePack index shape;
- standards-compliant Zstd RAW-block frames for the mandatory compressed index;
- redundant primary/tail indexes and commit footer.

It intentionally does **not** implement the full encoder policy or an independent browser reader. The
canonical project prefers a future WASM build of the shared native core over proliferating parsers. CI
therefore creates a browser-written archive and opens/reads it with the canonical Python reader.

The writer is hard-gated to the format revision it was reviewed against. A format bump must update and
re-test the writer; the website must never keep creating stale bytes under a new version label.

## Licensing status on the site

Apache-2.0 is currently a **proposal, not an adopted license**. Until `LICENSING.md` records adoption,
the site must use wording such as “proposed Apache-2.0 license” and must not claim that CMPCT is already
released under Apache-2.0.

## Build locally

```bash
python tools/check_public_surface.py
python site/build_site.py --out _site
python -m http.server 8000 -d _site
```

For the browser writer gate:

```bash
node site/tests/browser-writer-smoke.mjs /tmp/browser-writer-smoke.cmpct
PYTHONPATH=src python -c "from pathlib import Path; from cmpct.reader import CMPCT; a=CMPCT(Path('/tmp/browser-writer-smoke.cmpct')); print([x[0] for x in a.files]); a.close()"
```

## Publication

`.github/workflows/pages.yml` validates the site on pull requests and ordinary `main` pushes, but
publication is deliberately manual while the project remains private/pre-presentation. A future
manual publish run can deploy through GitHub Pages once Pages is enabled and the repository/public-
surface review is complete.

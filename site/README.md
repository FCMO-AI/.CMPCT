# CMPCT website

This directory is the source for the CMPCT GitHub Pages site.

## Product role

The site is the human/agent front door for CMPCT: project explanation, current engine model, quick-start documentation, durable benchmark viewing, machine-readable agent orientation, a fixed-header inspector, and a conservative browser-side archive writer.

The site deliberately lives in `site/` rather than `docs/` so normative format documentation stays plain, reviewable repository material instead of becoming coupled to a website framework.

## FCMO visual behavior

The implementation follows the supplied FCMO identity principles rather than applying generic “tech” decoration:

- charcoal/white structure dominates; orange `#FD5204` is reserved for actions, crossings and state changes;
- grid, boundaries, alignment and negative space carry the composition;
- the caret acts as an operator/cursor that enters a system instead of as decorative wallpaper;
- motion is brief and mechanical;
- no gradients, neon, particle fields or faux terminal/data-stream spectacle;
- monospace appears only for actual commands/data, while the rest of the interface stays sober and editorial.

## Automatic canonical data

`build_site.py` reads the repository at deployment time and generates:

- `project-data.json` — project/version/format state plus durable ZIP-parity benchmark records;
- `agent.json` — machine-readable orientation and reading order;
- `llms.txt` — compact agent/human orientation;
- build-time version/revision markers in the page itself.

Every push to `main` rebuilds the Pages artifact, so a CMPCT version change in `pyproject.toml`, a format revision change in `src/cmpct/codec.py`, or a new durable parity record becomes visible without manually editing website numbers.

## Browser writer safety boundary

`assets/cmpct-browser-writer.js` emits a real revision-24 CMPCT subset for regular files:

- direct RAW or raw-DEFLATE blobs;
- SHA-256 identity and CRC32 checks;
- exact-content deduplication;
- revision-24 MessagePack index shape;
- standards-compliant Zstd RAW-block frames for the mandatory compressed index;
- redundant primary/tail indexes and commit footer.

It intentionally does **not** implement the full encoder policy or an independent browser reader. The canonical project prefers a future WASM build of the shared native core over proliferating parsers. CI therefore creates a browser-written archive and opens/reads it with the canonical Python reader.

The writer is hard-gated to the format revision it was reviewed against. A format bump must update and re-test the writer; the website must never keep creating stale bytes under a new version label.

## Build locally

```bash
python site/build_site.py --out _site
python -m http.server 8000 -d _site
```

For the browser writer gate:

```bash
node site/tests/browser-writer-smoke.mjs /tmp/browser-writer-smoke.cmpct
PYTHONPATH=src python -c "from pathlib import Path; from cmpct.reader import CMPCT; a=CMPCT(Path('/tmp/browser-writer-smoke.cmpct')); print([x[0] for x in a.files]); a.close()"
```

## GitHub Pages

`.github/workflows/pages.yml` validates the site on pull requests and publishes the built artifact on `main`. GitHub Pages must use **GitHub Actions** as the repository's Pages source; that is a one-time repository setting, not website source code.

Publication visibility is an organization/repository Pages policy. Do not infer that a Pages deployment is private merely because this repository is private.

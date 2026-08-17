# Site agent instructions

This subtree is CMPCT's public proof surface. Before modifying it, read:

1. `../docs/SITE_PUBLIC_PROOF_STANDARD.md`;
2. `../docs/GH_PAGES_DEPLOYMENT.md`;
3. `README.md`;
4. `../docs/PUBLIC_SURFACE.md`;
5. `../docs/BENCHMARKS.md`;
6. the current public benchmark record(s) under `../benchmarks/history/`.

## Non-negotiables

- Do not type benchmark headline percentages into HTML or CSS.
- Consume `project-data.json.public_evidence` for release-independent performance presentation.
- Do not add a new `frontier-vXYZ.js` renderer for each release. Normalize the new benchmark schema into
  `cmpct-public-evidence-v1` instead.
- Keep at least one familiar baseline and the strongest relevant serious compressor visible when evidence exists.
- Preserve relevant losses on the Red Team Board. Green means measured favorable evidence, not “CMPCT.”
- Keep research-frontier authority visually and textually separate from canonical format/reader authority.
- Raw stored-byte comparison does not imply equivalent access, recovery, integrity or durability semantics.
- Browser Lab compatibility is a release-sensitive feature; do not weaken its revision gate.
- Preserve accessibility, mobile reading order and `prefers-reduced-motion` behavior.
- Presentation-only work advances `SURFACE_REVISION`, not the numeric core version.
- Run `python site/tests/proof_surface_contract.py _site` after building the site.
- Run `python site/tests/release_evidence_contract.py` before promoting a static site tree.

## Publication architecture

- `main` owns canonical site source, benchmark evidence, generators, tests and documentation.
- `gh-pages` owns generated static serving artifacts only. Never develop there or hand-edit benchmark claims there.
- GitHub Actions validates `main`; it must not be required to build an already-promoted `gh-pages` tree before serving.
- Every `gh-pages` promotion must include `.nojekyll`, `deployment.json`, `project-data.json`, `agent.json`,
  `llms.txt` and `surface-revision.txt` alongside the browser assets.
- `deployment.json.source_commit` must identify the exact `main` commit used for the static tree.
- Pages repository settings are expected to use **Deploy from a branch → gh-pages → / (root)**.
- A workflow may audit or validate publication, but do not restore `actions/deploy-pages` as the default serving path
  without an explicit architecture decision.

A future agent should be able to replace the current benchmark record with the next release's evidence and
see the hero, arena, loss board and receipt update without rewriting the page. Publication should then be a
validated static promotion, not a second implementation of the website.

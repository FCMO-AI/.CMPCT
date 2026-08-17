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

## Mandatory publication triggers

A static-site promotion is required after merge whenever a change affects any public output or the data that drives it. This includes:

- `site/**` source, renderer, Browser Lab, accessibility, design or copy changes;
- `SURFACE_REVISION`;
- a numeric CMPCT project-version change;
- a canonical on-disk format-revision change;
- a new or superseding durable public benchmark record under `benchmarks/history/`;
- release/frontier/current-state changes that alter what the website should say;
- capability authority, benchmark-policy, or public-evidence schema/normalization changes.

Do not decide that publication is unnecessary merely because HTML itself did not change. The website is evidence-driven, so new release/evidence state can change the generated artifact without a source-template edit.

## Definition of done for site-affecting work

Site-affecting work is **not complete** when the PR merely merges to `main`. Completion requires:

1. merge the canonical source/evidence change to `main`;
2. materialize the site from that exact resulting `main` commit;
3. run every required gate in `../docs/GH_PAGES_DEPLOYMENT.md`;
4. promote the complete generated tree to `gh-pages` without merging the source tree into it;
5. write/update `deployment.json` so its `source_commit`, project version, surface revision, format revision and evidence schema identify the promoted state;
6. verify the live public URL serves that receipt and the expected visible markers/data.

If `gh-pages/deployment.json` still identifies an older site-relevant source state, the website is stale and the task remains incomplete. A green CI run, a merged PR, or a populated `gh-pages` branch is not equivalent to a verified live deployment.

If the agent lacks permission to promote or cannot verify the live site, it must explicitly report the exact missing publication step and must not claim the site is current, deployed, released, or live.

## New-version rule

Every new numeric CMPCT release must update the public site as part of release completion. The promoted site must expose the new project version and its current committed evidence while retaining the canonical-vs-research boundary and visible losses. Never leave a newly released CMPCT version on `main` while knowingly serving an older version/frontier on `gh-pages`.

A future agent should be able to replace the current benchmark record with the next release's evidence and
see the hero, arena, loss board and receipt update without rewriting the page. Publication should then be a
validated static promotion, not a second implementation of the website.

Footnote: `gh-pages` is deliberately a deployment branch, not a development branch. Keeping the two roles separate makes rollback and provenance simple while allowing all substantive validation to remain attached to canonical `main`.
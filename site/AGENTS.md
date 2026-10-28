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

## Visual quality contract

The pre-public-proof visual grammar restored in Surface 0.29.f is a **minimum quality floor**, not an archive curiosity. Future content or engineering work must adapt itself to that visual system unless a deliberately reviewed replacement is demonstrably stronger.

The following features may evolve, but they may not silently disappear or collapse into generic cards:

- the intricate mixed sans/serif hero composition and strong typographic pacing;
- a dominant authored hero graphic tied to CMPCT or its evidence, not generic decorative particles;
- the proof score as a major visual object rather than a small dashboard tile;
- the information-graph chapter and its relationship choreography;
- the full-width light canonical/research authority break;
- the performance arena as a measured visual instrument;
- deliberate chapter pacing, responsive composition and a visually finished Browser Lab.

Every visual edit must be **rendered and inspected**, not approved from source code alone. The minimum manual anchor remains:

- desktop: 1440×1000;
- mobile: 390×844;
- the hero/proof score;
- arena + Red Team Board;
- information graph;
- canonical/research authority band;
- Browser Lab;
- any region directly changed by the patch.

Surface 0.29.h adds a machine-enforced physical viewport matrix. Any site-affecting PR must also pass
`site/tests/viewport-matrix.mjs` through the public-proof workflow. The matrix deliberately covers width,
height **and aspect ratio**, not just familiar device labels:

- 320×568 compact phone;
- 360×800 standard phone;
- 390×844 tall phone;
- 430×932 large phone;
- 844×390 landscape phone;
- 540×720 foldable/narrow inner display;
- 768×1024 and 820×1180 tablet portrait;
- 1024×768 tablet landscape;
- 1024×600 short panel;
- 1366×768 short laptop;
- 1440×900 16:10 laptop;
- 1280×1024 5:4 desktop;
- 1920×1080 desktop;
- 2560×1080 ultrawide;
- 2560×1440 large desktop.

The browser gate must retain screenshot artifacts and fail on document-level horizontal overflow, clipped
proof values, wide-layout hero collisions, header collisions, information-graph node collisions, collapsed
required surfaces, or impractically small controls. Those assertions are a floor, not a substitute for visual
judgment: inspect the screenshots when a visual change is material, and add an assertion whenever rendering
exposes a new concrete failure mode.

For large redesigns, compare the viewport artifact against the last accepted surface rather than checking only
whether the new screenshots are internally valid. A CSS/JS feature that exists in source but is visually hidden,
clipped, illegible, compositionally weaker, or broken at an untested ratio counts as a failed feature.

Visual changes must obey a quality ratchet:

1. first reproduce the current/baseline surface;
2. make one coherent change;
3. render it at the required viewports;
4. compare against the baseline for hierarchy, legibility, distinctiveness and product meaning;
5. keep the change only if it survives that comparison;
6. preserve a regression assertion for any concrete defect discovered.

Do not confuse technical spectacle with quality. WebGL, canvas, shaders, scroll choreography or large motion are welcome when they explain CMPCT or create a stronger authored experience; they are not intrinsically better than a simpler effect. Secondary UI must not compete with the main idea. Reduced-motion must retain the composition and information even when choreography is removed.

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

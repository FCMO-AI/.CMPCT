# Static GitHub Pages deployment

Status: **normative publication architecture for the CMPCT public website.**

## Authority split

- `main` is the only canonical source for website HTML/CSS/JS, benchmark evidence, generator code, tests and documentation.
- `gh-pages` is generated serving output. Do not develop on it, hand-edit claims on it, or treat it as a second source of truth.
- GitHub Actions remains a validation system. It is intentionally not the publication dependency for an already-promoted static tree.

This separation means a hosted-runner backlog may delay CI feedback, but it does not require the public website to be rebuilt by a custom workflow before GitHub can serve a previously validated static promotion.

## Required validation before promotion

From a clean checkout of the intended `main` commit:

```bash
python tools/check_public_surface.py
python site/build_site.py --out _site
python site/enhance_site.py _site
python site/tests/proof_surface_contract.py _site
python site/tests/release_evidence_contract.py
node --check site/src/assets/app.js
node --check site/src/assets/experience.js
node --check site/src/assets/motion.js
node --check site/src/assets/cmpct-browser-writer.js
node site/tests/browser-writer-smoke.mjs /tmp/browser-writer-smoke.cmpct
```

The canonical-reader smoke test in `.github/workflows/site-proof-contract.yml` remains part of CI as well.

## Static branch contract

A promoted `gh-pages` tree must contain, at minimum:

- `index.html`;
- all browser assets referenced by the page;
- `project-data.json` using `cmpct-public-evidence-v1`;
- `agent.json` and `llms.txt`;
- `surface-revision.txt`;
- `deployment.json` naming the exact `main` source commit;
- `.nojekyll`.

`deployment.json` is the publication receipt. Live-site verification must compare its `source_commit`, `surface_revision`, format revision and evidence schema with the intended source release.

## GitHub Pages setting

Repository Pages must use:

- Source: **Deploy from a branch**;
- Branch: **`gh-pages`**;
- Folder: **`/ (root)`**.

GitHub internally performs the final Pages server deployment even for branch publishing. `.nojekyll` tells that path the branch is already-built static output, avoiding a project build/Jekyll stage. That internal deployment is infrastructure, not CMPCT's build or validation pipeline.

## Promotion procedure

1. Make source/evidence changes on `main` through the normal review and validation process.
2. Materialize the deterministic static site from that exact commit.
3. Run the proof, release-evidence, disclosure, JavaScript and Browser Lab gates above.
4. Replace the `gh-pages` tree with that generated output; never merge arbitrary source-tree files into it.
5. Write/update `deployment.json` with the source commit and surface revision.
6. Push the static tree to `gh-pages`.
7. Verify the public URL serves the deployment receipt and visible markers expected from that commit.

## Automation rule

Do not reintroduce a custom Pages build/deploy workflow merely for convenience. A workflow may validate source or audit a published tree, but serving must remain branch-backed unless the repository deliberately changes this architecture.

Footnote: GitHub documents that commits pushed to a Pages source branch by a workflow using the repository `GITHUB_TOKEN` do not trigger a Pages build. Therefore a future automatic promoter must use an explicitly authorized publication credential or a supported Pages deployment API. It must not silently assume that a `GITHUB_TOKEN` push is equivalent to a human/agent Git promotion.

## Rollback

Rollback is a Git operation: move `gh-pages` to a previously verified static deployment commit. The canonical `main` history is not rewritten merely to roll back presentation serving.

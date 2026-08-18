# Static GitHub Pages deployment

Status: **normative publication architecture for the CMPCT public website.**

## Authority split

- `main` is the only canonical source for website HTML/CSS/JS, benchmark evidence, generator code, tests and documentation.
- `gh-pages` is generated serving output. Do not develop on it, hand-edit claims on it, or treat it as a second source of truth.
- GitHub Actions remains a validation system. It is intentionally not the publication dependency for an already-promoted static tree.

This separation means a hosted-runner backlog may delay CI feedback, but it does not require the public website to be rebuilt by a custom workflow before GitHub can serve a previously validated static promotion.

## Publication is part of completion

A merge to `main` is not, by itself, a website deployment. A populated `gh-pages` branch is not, by itself, proof that the public URL is current. A green validation workflow is not, by itself, publication.

For every site-relevant change, completion is the full chain:

**canonical change on `main` → deterministic build → validation → static promotion to `gh-pages` → live verification.**

Agents must not say “released”, “published”, “deployed”, “live”, “site updated”, or equivalent if that chain is incomplete.

### Changes that require a new static promotion

Promotion is mandatory after merge when any of the following changes the public artifact or the evidence it should render:

- `site/**` source, styles, scripts, Browser Lab code, accessibility behavior, design or copy;
- `SURFACE_REVISION`;
- the numeric CMPCT project version;
- the canonical on-disk format revision;
- durable public benchmark evidence under `benchmarks/history/`;
- release/frontier/current-state information exposed by the site;
- public capability authority, benchmark policy, public-evidence schema or normalization logic.

The trigger is semantic, not merely path-based. Evidence-driven output can require publication even when `index.html` itself did not change.

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

Do not promote a static tree whose required validation is red. If runner congestion prevents CI from completing but equivalent required checks are executed independently and reproducibly on the exact intended source commit, document that evidence explicitly in the promotion/release record; do not silently pretend queued CI is green.

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

A promotion should create a new `gh-pages` deployment commit whose parent is the previously verified `gh-pages` deployment while replacing the serving tree with the newly generated artifact. Never merge `main` wholesale into `gh-pages`; source files that are not part of the generated site do not belong in the serving branch.

## GitHub Pages setting

Repository Pages must use:

- Source: **Deploy from a branch**;
- Branch: **`gh-pages`**;
- Folder: **`/ (root)`**.

GitHub internally performs the final Pages server deployment even for branch publishing. `.nojekyll` tells that path the branch is already-built static output, avoiding a project build/Jekyll stage. That internal deployment is infrastructure, not CMPCT's build or validation pipeline.

## Promotion procedure

1. Make source/evidence changes on `main` through the normal review and validation process.
2. Merge them first; resolve the exact resulting `main` commit that is intended to be public.
3. Materialize the deterministic static site from that exact commit. Do not stamp a pre-merge PR head into `deployment.json` when the release is meant to represent the merged `main` state.
4. Run the proof, release-evidence, disclosure, JavaScript and Browser Lab gates above.
5. Confirm generated `project-data.json` and visible surfaces reflect the intended project version, format revision, frontier/evidence and losses. Missing current evidence must render unavailable rather than recycling stale claims.
6. Replace the `gh-pages` serving tree with the generated output; never merge arbitrary source-tree files into it.
7. Write/update `deployment.json` with at least the exact source commit, project version, surface revision, format revision and evidence schema.
8. Commit/push the static tree to `gh-pages`.
9. Verify the public URL serves the new deployment receipt and visible markers expected from that commit.
10. Only after the live verification succeeds may the site-affecting task or release be described as fully published.

## New-version completion rule

A numeric CMPCT release is not fully released while the public site knowingly serves an older project version/frontier or an older site-relevant evidence state.

For every new core version, the release dossier must therefore include evidence that:

- the durable public benchmark record(s) are committed on `main`;
- the stable public-evidence normalization renders the new release correctly;
- the generated site passed its proof/release/browser gates;
- `gh-pages/deployment.json` identifies the intended merged `main` source state;
- the live URL exposes that version and its correct canonical-vs-research authority boundary.

If publication is blocked by permissions or external infrastructure, report the release/site as **publication incomplete** and preserve the exact remaining step. Do not downgrade this to a cosmetic follow-up.

## Surface-only completion rule

Presentation-only work follows the same publication chain but uses `SURFACE_REVISION` rather than inventing a numeric core release. A coherent surface milestone is complete only when the corresponding generated static tree is live and its receipt exposes the intended surface revision.

## Freshness rule

Treat the website as stale when `gh-pages/deployment.json` predates the latest site-relevant merged `main` state. Freshness is semantic rather than “latest commit wins”: an unrelated repository commit need not trigger a rebuild, but any change affecting rendered source, public evidence, release/version identity, format identity, Browser Lab compatibility, or exposed public documentation does.

When uncertain, rebuild from current `main`, run the contract tests, compare the resulting artifact, and promote if the public output or receipt must change. Prefer a harmless verified refresh over knowingly leaving version/evidence ambiguity.

## Automation rule

Do not reintroduce a custom Pages build/deploy workflow merely for convenience. A workflow may validate source or audit a published tree, but serving must remain branch-backed unless the repository deliberately changes this architecture.

Footnote: GitHub documents that commits pushed to a Pages source branch by a workflow using the repository `GITHUB_TOKEN` do not trigger a Pages build. Therefore a future automatic promoter must use an explicitly authorized publication credential or a supported Pages deployment API. It must not silently assume that a `GITHUB_TOKEN` push is equivalent to a human/agent Git promotion.

## Rollback

Rollback is a Git operation: move `gh-pages` to a previously verified static deployment commit. The canonical `main` history is not rewritten merely to roll back presentation serving.

After rollback, verify the public URL and receipt exactly as for a forward promotion. A rollback that exists only as a branch move but has not reached the live site is not complete.

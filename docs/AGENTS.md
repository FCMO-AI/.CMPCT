# Documentation and release agent instructions

These rules extend the repository-root `AGENTS.md` for work under `docs/`.

## Release-to-site completion invariant

Any change that creates, advances, or materially redefines a CMPCT release must treat the public website as part of the release artifact, not as optional follow-up work.

This rule is triggered whenever work under `docs/` does any of the following:

- adds or changes `docs/releases/vX.Y.0.md`;
- changes the canonical release/frontier description in `docs/CURRENT_STATE.md`;
- changes public benchmark interpretation, capability authority, format identity, or release policy in a way the website exposes;
- accompanies a numeric project-version change, on-disk format revision, or new durable public benchmark evidence.

When triggered, the agent MUST read `GH_PAGES_DEPLOYMENT.md` and `SITE_PUBLIC_PROOF_STANDARD.md` and include static-site publication in its definition of done.

### A release is not complete until all of these are true

1. The canonical source, release note, durable public evidence, and any format/current-state documentation are merged to `main`.
2. The website is built from the exact resulting `main` commit, not from an earlier PR head or stale local checkout.
3. The public-surface, proof-surface, release-evidence, JavaScript, Browser Lab, and canonical-reader checks required by `GH_PAGES_DEPLOYMENT.md` pass for that source state.
4. The generated site reflects the new project version/frontier/format/evidence without hand-copied benchmark claims or stale fallback data.
5. The generated tree is promoted to the root of `gh-pages`, with `.nojekyll` and a `deployment.json` receipt whose `source_commit` is the exact `main` commit used to generate it.
6. The live GitHub Pages URL is checked after publication. Its `deployment.json`, `project-data.json`, visible release markers, surface revision, and canonical format revision must agree with the intended release.

If any required publication step cannot be performed because of permissions or external infrastructure, the agent must state that the release/site publication is **incomplete** and identify the exact unmet step. It must not say the release is fully published or the website is current.

## Staleness is a release defect

After a site-relevant release change lands on `main`, a `gh-pages/deployment.json` receipt that still points to an older site-relevant source state is considered deployment debt. Do not close or describe the release as complete while knowingly leaving that debt unresolved.

A newer unrelated `main` commit does not by itself make the site stale. Freshness is semantic: the deployment must include the latest commit whose changes affect rendered site source, public evidence, release/version identity, Browser Lab compatibility, or public documentation exposed by the site.

## Authority boundary

- `main` remains the source of truth.
- `gh-pages` remains generated serving output only.
- Never develop release logic or benchmark claims directly on `gh-pages`.
- Never merge `main` wholesale into `gh-pages`; replace the serving tree with the validated generated artifact and preserve deployment history as deployment commits.
- GitHub Actions may validate release/site state, but successful validation does not itself mean the public website was promoted or verified.

Footnote: this nested instruction exists so release-document work necessarily inherits the live-site completion requirement even when the implementation task did not begin inside `site/`.
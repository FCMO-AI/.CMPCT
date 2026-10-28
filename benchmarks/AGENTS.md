# Benchmark agent instructions

These rules extend the repository-root `AGENTS.md` for work under `benchmarks/`.

## Public-evidence publication invariant

A durable public benchmark record can change the generated website even when no HTML/CSS/JavaScript source changed. Therefore any change under `benchmarks/history/` that adds, supersedes, or materially reinterprets evidence consumed by the public site MUST include website freshness in its definition of done.

Before completing such work, read:

- `../docs/BENCHMARKS.md`;
- `../docs/SITE_PUBLIC_PROOF_STANDARD.md`;
- `../docs/GH_PAGES_DEPLOYMENT.md`.

After the evidence change is merged to `main`:

1. build the website from the exact resulting `main` commit;
2. run the disclosure, proof-surface, release-evidence, JavaScript, Browser Lab, and canonical-reader validation required by `docs/GH_PAGES_DEPLOYMENT.md`;
3. confirm the generated `cmpct-public-evidence-v1` state uses the new evidence where applicable and does not preserve a stale headline merely to avoid missing data;
4. promote the complete generated tree to `gh-pages` with an updated `deployment.json` receipt;
5. verify the live Pages URL serves the expected evidence/version/frontier and still exposes relevant losses and scope qualifications.

A benchmark/evidence task is not fully complete while the public site knowingly serves an older site-relevant evidence state. If promotion or live verification cannot be performed, report the publication as incomplete and name the exact blocker rather than claiming the evidence/site update is fully released.

Never edit benchmark numbers directly on `gh-pages`. `main` and its durable benchmark history remain the authority; `gh-pages` is only the generated projection of that authority.

Footnote: this nested rule prevents evidence-only work from bypassing the site completion contract simply because the site templates themselves did not change.
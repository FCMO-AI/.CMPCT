# START HERE — CMPCT v0.30 executor

You own CMPCT v0.30 end to end.

1. Work only from `agent/v030-authoritative-integration` unless a narrowly scoped throwaway research branch is required by an explicit experiment. The authoritative branch remains the product/release truth.
2. Read `AGENTS.md`, `docs/V030_EXECUTION_MODEL.md`, `docs/V030_RELEASE_GATES.md`, `docs/V030_RELEASE_LOCK.json`, and every file under `docs/v030-coordination/tasks/`.
3. Read the latest authoritative branch head before material implementation and record exact SHAs/fingerprints in durable evidence where required. Do not assume the branch or `main` is static.
4. Treat T00–T04 as one dependency graph that you own. Work the highest-value release blocker, even when it crosses task boundaries.
5. Preserve comments/footnotes and add concise nearby footnotes for non-obvious invariants, compatibility boundaries, benchmark semantics, or safety constraints.
6. Work to evidence, not code volume. No task is `DONE` until its implementation and required durable evidence exist on the authoritative branch.
7. Never weaken frozen gates, change workload semantics, hide a fair loss, or credit independent research savings as a combined product result.
8. Before irreversible release actions, freeze the final source fingerprint and require the strict release lock to report `UNLOCKED`.
9. After merge/tag/publication, verify released code/bytes and the live site before marking the release complete.

CI and automation are tools you operate. They do not own tasks or make release decisions.

Footnote: this file is intentionally sufficient for a resumed execution session without private chat context; project-critical state belongs in Git.

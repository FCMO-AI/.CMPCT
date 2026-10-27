# J24G01 — Source-exact PR integration topology, prospective protocol

Date: 2026-10-27 UTC. Baseline: released CMPCT v0.30.0/r24, \`main@80c358f8824ec1b20d349c92ed94c898090969b0\`; active unmerged \`agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b\`. This is **integration evidence-enablement only**, not a product-performance or release claim.

## Observation and decision
The live CMPCT repository contains hundreds of concurrent draft PRs. Several independently valid Reader fixes mutate the same file or are stacked on another experimental branch, creating a risk of duplicate implementation and blind integration. A human-/agent-usable *live GitHub-derived* dependency and shared-mutation map, with exact head refs, could make the next safe integration decision materially cheaper.

## Prospective hypothesis and simpler control
A stateless, bounded GitHub API tool can:
1. reconstruct the actual parent/child PR graph by **base branch == another open PR head branch**;
2. distinguish **overlapping code-path surfaces** from true merge conflicts (same path does not prove conflict);
3. identify same-code overlaps that are **expected stacks** versus **non-ancestor parallel PRs** needing explicit reconciliation;
4. produce machine-readable time-scoped facts from live PR head SHAs without becoming a second project-state database;
5. never label an unexecuted merge, release or CI gate as safe/green.

**Simpler control:** manually inspect GitHub PR lists and filenames. Accept this tool only if it returns the same exact parent/parallel judgments on the observed selected eight-PR sample, survives synthetic adversarial branch cycles and absent parents, and remains read-only with bounded fetches. The human/agent can continue to use GitHub directly if this tool fails.

## Original pilot sample, observed before code
Selected #574, #569, #609, #615, #613, #601, #614, #608. From current live GitHub PR file listings:
- #569/#609/#613/#601 all modify \`src/cmpct/reader.py\` on different source lineages; this is **shared mutation surface**, not necessarily patch conflict;
- #609/#615 modify \`src/cmpct/validation.py\`, not a proven conflict;
- #608/#614 modify \`native/cmpct_cdc.c\`, but #614 is **an intentional child of #608** and should be classified as inherited/stacked, not an independent collision;
- #574 edits only the Discovery documents in this sample; this does not mean its CI or release eligibility is green.

## Kill/narrow conditions
- Misidentify #614/#608 as independent colliding implementations, invent an ancestry edge for unrelated heads, or show mergeable/green without actual git merge and exact-head CI: tool is rejected.
- Repeated calls consume unbounded GitHub API quota; hidden mutation, authentication secret echo, stale cache claimed as lock, or line-level merge claims from filename-only evidence: tool is rejected.
- If output is merely GitHub's existing PR table with no independently verifiable causal graph/overlap distinction, retire rather than maintain it.

## Evidence ladder and expected boundary
First implement pure classification on a frozen in-memory fixture; then GitHub Actions Linux stdlib tests; then opt-in *read-only* hosted live pilot against the exact PR list with timestamp/head identities, and compare against independently fetched provider results. No automatic merge, branch update, PR closure, release or modification to \`STATE.json\`; Discovery state has its own #574 owner. Source/CI evidence and conclusions must distinguish infrastructure-enablement from product progress.

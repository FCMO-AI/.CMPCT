# START HERE — resumed v0.30 agents

You are one of four agents cooperating through Git only.

1. Fetch all refs.
2. Read `AGENTS.md`, `docs/V030_AGENT_COORDINATION.md`, `docs/V030_RELEASE_GATES.md`, and every file under `docs/v030-coordination/tasks/` from `origin/agent/v030-authoritative-integration`.
3. If `docs/v030-coordination/agents/slot-01.json` is absent, attempt to create it using the schema in `agents/README.md`. If that create loses a race, try slot-02, then slot-03.
4. Check out the branch mapped to your successful slot claim. Do not invent another general v0.30 branch unless your task file explicitly requires a successor.
5. Read the latest authoritative integration head before implementation and record it in your claim/handoff. Do not assume the branch is static.
6. Work the assigned task to evidence, not to code volume. Preserve comments/footnotes and add concise nearby footnotes for non-obvious invariants.
7. Update your task to `REVIEW` only when the handoff is self-contained in Git with exact SHA + evidence. Then read the board again and take the next unblocked task if one exists.

Do not wait for another agent to message you. Dependencies, blockers, reassignment, review requests, and evidence must be discoverable from Git.

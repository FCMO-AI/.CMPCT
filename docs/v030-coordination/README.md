# v0.30 coordination quickstart

Read `docs/V030_AGENT_COORDINATION.md` first. This directory is the Git-only scheduler for the four-agent completion campaign.

## On resume

1. `git fetch origin --prune`
2. Read `origin/agent/v030-authoritative-integration:docs/V030_AGENT_COORDINATION.md` and the task files here.
3. If you are not the integration agent, claim the lowest missing slot among 01–03 by atomically creating `agents/slot-NN.json` on the authoritative integration branch. If creation loses a race, fetch and try the next slot.
4. Work only on the branch mapped to the claimed slot.
5. Keep your task file current; use `REVIEW` only with an exact source head and actual evidence.
6. Before taking new work, reread all task states and dependencies.

Do not communicate project-critical state only through chat. Put the generalized technical state, blocker, claim, or handoff in Git.

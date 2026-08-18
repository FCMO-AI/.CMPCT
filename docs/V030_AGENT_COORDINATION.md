# CMPCT v0.30 Git-only multi-agent coordination

This document is the coordination contract for the four-agent v0.30 completion campaign.

The agents do not need direct agent-to-agent messaging. Git is the coordination bus: branches carry implementation, task files carry ownership/state, commits carry handoffs, and durable benchmark records carry evidence.

## Mission

Finish v0.30 as a coherent release-quality system without duplicate promoted implementations, stale-branch overwrite, hidden regression debt, or benchmark claims borrowed from independent research artifacts.

Production remains v0.29.0 / r24 until the v0.30 release lock is satisfied.

## Roles

Four logical slots exist. Slot identity is a coordination convenience, not a permanent person/agent identity.

- **slot-00 — integrator/release referee**: owns `agent/v030-authoritative-integration`, reconciliation with `main`, conflict adjudication, release-lock truth, and final integration. This slot is already occupied by the current convergence agent.
- **slot-01 — native/portability**: owns r25 native/shared-reader parity, independent golden vectors, recovery/fuzz/native ABI, ZIP/export, platform/Android portability evidence.
- **slot-02 — evidence/performance**: owns authoritative 15-workload evidence, shared-build rehabilitation, create/extract/selective-read/RSS measurement, external competitor matrix, and evidence harvesting. It may fix benchmark harness/runtime instrumentation but must not weaken frozen thresholds.
- **slot-03 — graph/productization**: owns promoted graph architecture cleanup, PrefixGraph internalization or an explicit justified alternative, canonical API/CLI surface, research-to-product consolidation, format documentation, and removal of redundant promoted implementations after evidence is preserved.

A slot may reassign a subtask to another slot only by changing the relevant task file or adding a dependency/handoff commit. No verbal/chat handoff is required.

## Atomic slot claim

The three resumed agents claim slots 01–03 using Git itself:

1. Fetch `main` and read this file plus `AGENTS.md` and `docs/V030_RELEASE_GATES.md`.
2. Inspect `docs/v030-coordination/agents/` on `main`.
3. Try to create the lowest-numbered missing claim file among `slot-01.json`, `slot-02.json`, `slot-03.json` on `main` or on the dedicated coordination branch if direct-main writes are restricted.
4. A create conflict means another agent won that slot. Fetch and try the next missing slot. Do **not** overwrite an existing claim.
5. The successful claim file must record: slot, agent branch, claimed-at UTC timestamp, base integration SHA observed, and current task IDs.

Git object creation is the lock. No separate election protocol exists.

## Coding branches

Only slot-00 writes implementation directly to `agent/v030-authoritative-integration`.

Other slots use these dedicated branches, created from the integration head current at campaign start:

- `agent/v030-coop-native-portability`
- `agent/v030-coop-evidence-performance`
- `agent/v030-coop-graph-productization`

A non-integrator must not force-push or rewrite another slot's branch. If a branch needs a major restart, create a successor branch and record it in the slot claim/task file.

## Task files are the scheduler

`docs/v030-coordination/tasks/*.md` are authoritative work packages. Each task contains:

- objective and owner slot;
- state: `READY`, `CLAIMED`, `BLOCKED`, `REVIEW`, `DONE`, or `REJECTED`;
- dependencies;
- owned paths / paths that must not be modified;
- exact completion evidence;
- latest relevant commit SHA;
- handoff notes / discovered follow-up tasks.

Agents should update only their own task file when possible. This avoids one shared-board merge hotspot.

### State rules

- `READY`: unblocked and available to its assigned slot.
- `CLAIMED`: active implementation exists on the owner's branch.
- `BLOCKED`: cannot proceed without another task/evidence; name the dependency exactly.
- `REVIEW`: implementation is complete enough for slot-00 to inspect/import; include source head and validation evidence.
- `DONE`: slot-00 imported/accepted it and the required evidence is durable on the authoritative branch.
- `REJECTED`: mechanism/approach failed its frozen test. Preserve the negative result and why.

A task is never `DONE` merely because its author says the code is finished.

## Work-stealing and reassignment

When a slot finishes its assigned task:

1. Mark it `REVIEW` with source head + exact evidence.
2. Read all task files.
3. Prefer the highest-priority `READY` task whose owned paths do not overlap an active task.
4. If none exists, create a new narrowly scoped task only when it closes a named release-gate gap or a newly discovered regression.
5. Do not create novelty/research branches merely to stay busy while release-critical work is available.

If another task is blocked on your result, that dependent task becomes the next priority after your handoff.

## Handoff contract

Every `REVIEW` handoff must be self-contained in Git and contain:

- source branch + exact head SHA;
- files intentionally changed;
- mechanism/invariant changed and what must not regress;
- commands/tests actually run and their result;
- durable benchmark/evidence paths if any;
- known losses/ambiguity/debt;
- whether on-disk bytes/API/ABI changed;
- integration instructions: merge whole commit, cherry-pick listed commits, or import specific blobs/files;
- conflicts expected with integration/main.

Commit messages should contain a short footnote when a non-obvious invariant or compatibility constraint drove the implementation.

## Conflict protocol

1. Never solve a conflict by blindly choosing `ours`/`theirs` for a promoted implementation.
2. Re-resolve both heads immediately before import.
3. Compare from the last reviewed source SHA, not from memory.
4. If two slots changed the same semantic owner, slot-00 selects one owner and ports only missing behavior/tests from the other.
5. Preserve negative evidence and useful tests from losing implementations.
6. Main reconciliation is slot-00-owned. Other slots do not independently merge `main` into the authoritative integration branch.

## Evidence hierarchy

Release authority, strongest to weakest:

1. durable benchmark/conformance record committed for the exact reconciled candidate;
2. successful CI artifact/run tied to that exact candidate SHA;
3. repeated controlled local measurement with recorded environment/raw data (preliminary only until accepted durably);
4. focused unit/property tests;
5. implementation/prose claims.

Historical green runs prove mechanisms, not the current release candidate.

## Frozen promotion invariants

No agent may weaken these to make a task pass:

- exact repaired 15-workload accepted-v0.29 aggregate identity;
- at least **687,783 B** aggregate saving;
- at least **3 improved workloads**;
- **0 inherited archive-byte regressions**;
- selected per-member decoded-context amplification **<=8x**;
- exact fallback/tie semantics;
- bounded hostile-input parsing and decode/materialization;
- create/extract/selective-read/RSS performance release gates;
- native/shared-reader parity for every promoted representation;
- exact external competitor matrix and honest semantics;
- public-surface/version/site/release gates.

## Integration rule

Parallel branches are allowed to be messy research/work branches. The authoritative branch is not.

Slot-00 may import only a reviewed, bounded slice of a source branch. The integration commit must preserve the source SHA and evidence provenance. Duplicate promoted implementations are a release blocker even if both work.

## Completion

All four agents should eventually converge to the same end state: no `READY`/`CLAIMED`/`BLOCKED` release-critical tasks, every normative release gate closed on the reconciled exact candidate, one canonical implementation per semantic responsibility, `main` merged and tagged, and public release/site evidence derived only from durable accepted records.

Footnote: the coordination files are process state, not benchmark evidence and not a numeric-version reason. They exist so autonomous agents can cooperate safely through Git without relying on chat history or hidden memory.

# Discovery Engine concurrency protocol

**Status:** normative coordination law for concurrent autonomous/recurrent CMPCT research activations. Subordinate to repository authority, frozen evidence, release law, and hard correctness/safety invariants.

## Why this exists

CMPCT's scheduled activations can overlap with human work, CI, and other agent activations. Git already provides durable concurrency primitives. The Discovery Engine must use them rather than pretending a shared mutable JSON file is a lock.

The goal is **useful concurrency without duplicated science**: multiple activations may progress independent questions, but no activation may silently overwrite another activation's discovery state, prediction, evidence, or decision.

## Two planes

### 1. Append-only scientific history

`research/discovery_episodes.jsonl` is the durable causal history. Predictions/outcomes/lessons are append-only. Existing observed events are never rewritten to resolve a conflict.

Concurrent activations should prefer new episode IDs and additive events. If two activations independently test the same question, preserve both results and explicitly reconcile them; do not delete one as redundant after observing it.

### 2. Compact frontier cache

`docs/discovery/STATE.json` is a **cache/index of current intent**, not scientific authority and not a lock. It may become stale immediately after another activation lands.

Every writer must:
1. read current authoritative branch/head and current state immediately before editing;
2. reconcile any intervening commits/PRs/episode events;
3. make the smallest semantic patch;
4. re-read after write when subsequent work depends on the new state;
5. never force-push or overwrite a concurrent state update merely to restore its earlier view.

If a clean semantic merge is not possible, leave STATE stale, preserve the scientific work elsewhere, and record the reconciliation need. Stale cache is safer than destroyed evidence.

## Claim protocol

A claim is advisory coordination, never exclusive authority.

For material work that can plausibly collide, create or reuse a durable GitHub branch/PR whose title/body identifies:
- discovery episode/question ID when one exists;
- solution family;
- exact starting authority SHA;
- scope expected to mutate;
- decisive question / kill condition.

Before substantial implementation, search current open PRs/branches and unresolved discovery episodes for the same family/scope/question.

A claim is **active** only while its branch/PR shows recent material work or a durable independent job is running. An abandoned claim does not reserve a scientific area forever.

### Collision handling

If another activation owns the same narrow mutation surface:
- do not create a second competing implementation by default;
- review its evidence and either continue that branch when safe, choose a dependency-safe adjacent experiment, or attack the hypothesis with an independent control;
- if independent replication is scientifically valuable, label it explicitly as replication before observing the result.

Different hypotheses may run concurrently when their mutations/evidence are separable. Concurrency should increase information gain, not branch count.

## Episode IDs

Use collision-resistant, human-readable IDs:

`E-YYYYMMDDTHHMMSSZ-<short-start-sha>-<family-slug>`

If an activation continues an unresolved episode, reuse its ID. Never mint a fresh ID merely because the scheduler fired again.

A prediction is immutable after its result is observed. Corrections are additive events.

## State reconciliation

When rebuilding STATE from concurrent truth, use this precedence:

1. hard repository/release/frozen law;
2. directly observed product/evidence receipts on the current relevant SHA;
3. append-only discovery outcomes;
4. active PR/branch claims and pending independent jobs;
5. STATE.json's prior cached intent.

Conflicts at the same evidence level remain explicit until resolved. Never select the more convenient result.

## Pending work

A pending CI/runner/compute job must have enough durable identity for another activation to inspect it: provider/surface, run/job identifier or stable URL/reference when available, source SHA, question/episode ID, expected artifact, and what decision the result can unlock.

Do not represent a job as pending merely because an agent intended to launch it.

While independent work runs, choose another dependency-safe action. Poll only when the result is expected to have matured or when its result changes the next decision.

## Merge/rebase safety

Discovery infrastructure is not exempt from normal Git discipline.

- Re-read target files before late writes.
- Prefer small additive commits.
- Never force-update the authoritative frontier to resolve a Discovery Engine conflict.
- Never auto-resolve semantic conflicts in predictions, outcomes, benchmark identities, thresholds, or release evidence.
- If two infrastructure implementations overlap, PARETOBONK them and converge to the smaller coherent system; do not permanently maintain duplicate planners/ledgers/state machines.

## Zero-history handoff invariant

At any point, a future activation should be able to answer, from repository/GitHub truth alone:

1. What is authoritative now?
2. What material questions are actively claimed?
3. What evidence/jobs are pending?
4. Which hypotheses are unresolved, falsified, saturated, or protected?
5. What is the cheapest decisive unclaimed action?
6. What can I work on without colliding with another activation?

If it cannot, concurrency infrastructure is incomplete.

## Anti-bureaucracy

Do not create claims/episodes for trivial edits, obvious fixes, ordinary documentation, or work that cannot plausibly collide. The protocol exists to protect expensive scientific decisions and shared mutation surfaces.

Measure its value by fewer duplicate experiments, fewer lost/overwritten results, shorter handoff/reconstruction time, and more useful independent progress—not by number of claims or ledger events.

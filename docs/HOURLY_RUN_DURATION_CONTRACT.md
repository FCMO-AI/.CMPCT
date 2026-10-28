# Hourly Run-Duration Contract

Status: **normative for scheduled/autonomous CMPCT engineering activations**.

This is execution-process law. It does not change archive semantics, release gates, benchmark thresholds, `VERSION`, `SURFACE_REVISION`, or on-disk format revision, and it does not by itself justify any version/revision increment.

## Purpose

An hourly activation is a maximum-throughput engineering window, not a status check and not a one-ticket pass. The intended use of the window is sustained useful work until the handoff boundary, while preserving CMPCT's evidence and safety standards.

The duration floor is not permission for churn. Work must continue only through the highest-value safe work available under repository truth.

For material compression/performance/frontier work, `docs/RND_DOMINATION_RUBRIC.md` is also normative. The hour is not merely for closing whichever small ticket is easiest: it must allocate research effort according to the diagnosed strict gap, saturation state, radicality requirement, and research/productization queues defined there.

## Mandatory wall-clock protocol

1. **Record `T0` immediately at activation start.** Use an actual system/time source available to the agent. `T0` is per activation and must not be inherited from a prior run.
2. **Do not voluntarily finish before `T0 + 50 minutes`.** A primary task completing, becoming blocked, or entering a wait state does not end the activation.
3. **Check the wall clock at every major lane transition and before any attempted final response.** If elapsed time is below 50 minutes, the run is not complete unless an explicit early-exit exception below applies.
4. **From `T0 + 50m` through `T0 + 59m`, enter landing mode.** Finish the current safe unit, persist code/evidence, reconcile repository truth, re-check exact-head CI where relevant, and prepare the handoff. Do not start work likely to leave the branch inconsistent at the boundary.
5. **At or after `T0 + 59m`, start nothing new.** Persist any safe partial state/evidence and finish promptly so the next hourly activation can take over.

The normal permitted voluntary finish window is therefore **50–59 elapsed minutes**.

## Mandatory R&D selection checkpoint

Before material frontier work, recover the current strict ZIP/Zstd-19 matrix and applicable v0.29 runtime/RSS floors, then apply `docs/RND_DOMINATION_RUBRIC.md`:

1. classify the active red(s) D0–D5;
2. apply saturation triggers S1–S6;
3. identify the minimum admissible radicality R0–R4;
4. inspect recent/in-flight experiments so the same family is not repeated blindly;
5. score the best unblocked hypotheses with the Research Priority Score;
6. select from both the **frontier queue** (strict/structural gap) and **convergence queue** (proven-win productization/evidence) as repository truth warrants;
7. preserve the rolling-three-activation STRUCTURAL_RED R&D floor when it applies.

Near-boundary optimization remains correct when measured local cost can actually close the gap. Once a family meets a saturation trigger, continuing micro-optimization as the primary strategy is a contract violation unless new evidence changes the diagnosis.

## If primary work is done, blocked, or waiting

Do not idle and do not end early. Move immediately to the highest-value dependency-safe work that can be advanced without weakening evidence. Prefer, in order as repository truth warrants:

- finish the next honest D5/productization prerequisite for an already-proven strict win;
- advance the highest-RPS unblocked STRUCTURAL_RED hypothesis required by the domination rubric;
- inspect another release-critical red lane or exact failed log/artifact;
- implement/test an orthogonal safe fix;
- mine completed CI artifacts and reconcile stale evidence;
- strengthen deterministic regression, adversarial, recovery, locality, integrity, native, Android, portability, or performance coverage;
- reduce a known performance bottleneck when the rubric's micro-optimization admissibility test says that work can materially close the strict gap;
- prepare or run the next exact falsification/benchmark whose prerequisites are satisfied;
- derive an exact lower bound, impossibility proof, contribution oracle, or futility filter that can retire speculative losing work;
- reconcile `CURRENT_STATE`, evidence fingerprints, active PR truth, and handoff state;
- preserve a falsified result, apply S1–S6, and pivot to the next highest-value hypothesis rather than repeating the same family.

Waiting on CI is not idle time when another dependency-safe lane exists.

## Forbidden ways to satisfy the duration floor

The following do **not** count as useful continuation:

- sleeping or deliberately waiting for the clock;
- cosmetic edits, status prose, or commit splitting created only to consume time;
- rerunning unchanged expensive work without a diagnostic reason;
- repeating a saturated optimization family without new causal evidence merely because it is easy to edit;
- pursuing novelty for spectacle when a proven strict win only needs productization;
- weakening a benchmark, invariant, safety requirement, release gate, or evidence rule to manufacture progress;
- benchmark-identity dispatch or workload-specific production tuning;
- starting a large risky change near the landing boundary merely to remain busy.

If all productive safe work truly appears exhausted, perform a bounded repository/evidence/adversarial review and identify the next falsifiable engineering gap rather than idling.

## Early-exit exceptions

Finishing before 50 elapsed minutes is allowed only for:

- platform- or tool-enforced termination/hard execution limit;
- unrecoverable authorization/access failure that prevents all useful repository work;
- a genuinely unsafe state where continuing risks data, repository integrity, release integrity, or other protected invariants.

A failed CI job, saturated runner, missing optional execution surface, one blocked benchmark, or completion of the originally selected ticket is **not** an early-exit exception when dependency-safe work remains.

Never fabricate elapsed time or claim the contract was satisfied when the platform ended the run early.

## Handoff / audit requirement

Every scheduled/autonomous completion report must include compact duration telemetry:

```text
T0: <timestamp>
T_end: <timestamp>
elapsed: <minutes>
early_exit_exception: <none | exact external/unsafe reason>
```

If `elapsed < 50m` and `early_exit_exception` is `none`, the activation is not complete and useful work must continue.

The handoff must still prioritize engineering substance: exact head/branch/PR, work completed, measured evidence, blockers, exact-head CI truth, and next highest-leverage target.

When material R&D occurred, also include the compact domination audit required by `docs/RND_DOMINATION_RUBRIC.md`: strict target, D0–D5 diagnosis, R0–R4 radicality, active S1–S6 trigger, RPS, measured gap change, strongest surviving self-critique, terminal decision, and next decisive test. This is decision telemetry, not permission for a long status narrative.

## Interaction with CMPCT engineering law

Duration never outranks correctness. `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/RND_DOMINATION_RUBRIC.md`, release authority, evidence gates, hostile-input safety, portability, benchmark symmetry, zero-byte promotion regression, and all other canonical CMPCT laws remain fully binding.

The rule is simple: **use the available hour aggressively, but never buy utilization by lowering the standard of engineering—and never confuse activity with progress toward strict 15/15 domination.**

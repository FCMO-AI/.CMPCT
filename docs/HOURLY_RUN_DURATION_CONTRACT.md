# Hourly Run-Duration Contract

Status: **normative for scheduled/autonomous CMPCT engineering activations**.

This is execution-process law. It does not change archive semantics, release gates, benchmark thresholds, `VERSION`, `SURFACE_REVISION`, or on-disk format revision, and it does not by itself justify any version/revision increment.

## Purpose

An hourly activation is a maximum-throughput engineering window, not a status check and not a one-ticket pass. The intended use of the window is sustained useful work until the handoff boundary, while preserving CMPCT's evidence and safety standards.

The duration floor is not permission for churn. Work must continue only through the highest-value safe work available under repository truth.

## Mandatory wall-clock protocol

1. **Record `T0` immediately at activation start.** Use an actual system/time source available to the agent. `T0` is per activation and must not be inherited from a prior run.
2. **Do not voluntarily finish before `T0 + 50 minutes`.** A primary task completing, becoming blocked, or entering a wait state does not end the activation.
3. **Check the wall clock at every major lane transition and before any attempted final response.** If elapsed time is below 50 minutes, the run is not complete unless an explicit early-exit exception below applies.
4. **From `T0 + 50m` through `T0 + 59m`, enter landing mode.** Finish the current safe unit, persist code/evidence, reconcile repository truth, re-check exact-head CI where relevant, and prepare the handoff. Do not start work likely to leave the branch inconsistent at the boundary.
5. **At or after `T0 + 59m`, start nothing new.** Persist any safe partial state/evidence and finish promptly so the next hourly activation can take over.

The normal permitted voluntary finish window is therefore **50–59 elapsed minutes**.

## If primary work is done, blocked, or waiting

Do not idle and do not end early. Move immediately to the highest-value dependency-safe work that can be advanced without weakening evidence. Prefer, in order as repository truth warrants:

- inspect another release-critical red lane or exact failed log/artifact;
- implement/test an orthogonal safe fix;
- mine completed CI artifacts and reconcile stale evidence;
- strengthen deterministic regression, adversarial, recovery, locality, integrity, native, Android, portability, or performance coverage;
- reduce a known performance bottleneck without changing required semantics;
- productize an already-proven research win through its next honest prerequisite;
- prepare or run the next exact falsification/benchmark whose prerequisites are satisfied;
- reconcile `CURRENT_STATE`, evidence fingerprints, active PR truth, and handoff state;
- preserve a falsified result and pivot to the next highest-value hypothesis.

Waiting on CI is not idle time when another dependency-safe lane exists.

## Forbidden ways to satisfy the duration floor

The following do **not** count as useful continuation:

- sleeping or deliberately waiting for the clock;
- cosmetic edits, status prose, or commit splitting created only to consume time;
- rerunning unchanged expensive work without a diagnostic reason;
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

## Interaction with CMPCT engineering law

Duration never outranks correctness. `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, release authority, evidence gates, hostile-input safety, portability, benchmark symmetry, zero-byte promotion regression, and all other canonical CMPCT laws remain fully binding.

The rule is simple: **use the available hour aggressively, but never buy utilization by lowering the standard of engineering.**

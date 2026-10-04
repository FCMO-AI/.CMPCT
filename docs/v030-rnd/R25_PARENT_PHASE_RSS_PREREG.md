# r25 parent-phase RSS attribution — frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge R0 diagnostic / no release credit**

## Causal predecessor

`R25_CANDIDATE_PROCESS_ISOLATION_RSS_V2_RESULT.md` proved a real PrefixGraph lifetime lever on Shifted:
**400,958 -> 289,300 KiB (-27.8478%)**, with **1.179814x** wall-time debt.

`R25_DUAL_CANDIDATE_PROCESS_ISOLATION_RSS_RESULT.md` then proved that adding the same process boundary
around exact G0–G4 changes the remaining peak by only **38 KiB (0.0131266%)** and is therefore retired as
the primary explanation.

The residual ~289 MiB high-water occurs with one process alive. The next question is therefore not
"which child should be isolated?" but **which exact parent/product phase is active when the global
high-water is created?**

## Frozen question

On deterministic `resemblance_hostile_v1 / 01_shifted_versions`, under the accepted diagnostic
architecture where exact PrefixGraph executes in one disposable child and exits before exact G0–G4
continues in the parent, which product phase is active at the honestly charged whole-process-tree RSS
high-water?

This experiment changes no production source and grants no release credit.

## Instrumented phase labels

The diagnostic wraps only existing exact canonical call boundaries:

- `profile-prepare`: canonical `_prepare_profile_tree`;
- `r24-build`: canonical `_r24_build`;
- `r25-build`: canonical `_r25_build`;
- `g04-build`: exact canonical `RC.G04.build` in the parent;
- `publication`: canonical `_publish_atomic`;
- `final-verify`: canonical `strong_verify` invoked inside the complete product build.

Labels may overlap because the product intentionally runs genuine r24 and complete r25 work concurrently.
The sampler records the sorted active-label **signature** at every sample; it must not serialize or
reorder work merely to make attribution easier.

## Honest memory boundary

The decisive metric is sampled **whole live process-tree RSS**:

`parent VmRSS + VmRSS of every transitive descendant currently alive`

Sampling interval must be <=10 ms from immediately before complete `product.build` until it returns.
Every valid row requires >=100 samples and zero sampler errors. Parent `ru_maxrss` and per-signature
peaks are diagnostic; the global sampled whole-tree peak is authoritative for attribution.

## Exact identity and intervention proof

Every valid repetition must prove:

- exact canonical PrefixGraph, G0–G4 and reader semantic owners;
- exactly one PrefixGraph executor interception/submission/child, child success and exit before G0–G4;
- G0–G4 remains in the parent (no G0–G4 child);
- all phase wrappers and the executor are restored after the measured build;
- final selected representation, complete archive bytes/SHA-256, format revision, exact r24/r25 prices
  and strongly verified canonical filesystem tree are identical across repetitions;
- accepted repaired Shifted source identity is unchanged;
- no grammar, candidate eligibility, winner rule, locality/decode-unit rule, integrity/recovery rule,
  comparator, benchmark threshold, or release state changes.

Any identity or lifecycle mismatch invalidates the experiment.

## Repetitions

- three independent fresh-process repetitions;
- same accepted repaired Shifted source identity;
- same runner/dependency setup;
- same accepted PrefixGraph-isolated/G0–G4-parent topology;
- no release credit.

## Frozen interpretation

For each valid row, record the active phase signature at the **global whole-tree RSS peak**. Let the
three peak signatures be the evidence surface.

Apply the first matching rule:

1. if every peak signature contains `g04-build`: `RESIDUAL_PEAK_LOCALIZED_G04`;
2. else if every peak signature contains `final-verify`: `RESIDUAL_PEAK_LOCALIZED_FINAL_VERIFY`;
3. else if every peak signature contains `publication`: `RESIDUAL_PEAK_LOCALIZED_PUBLICATION`;
4. else if every peak signature contains `profile-prepare`: `RESIDUAL_PEAK_LOCALIZED_PROFILE_PREPARE`;
5. else if every peak signature contains `r24-build` and none contains `g04-build`:
   `RESIDUAL_PEAK_LOCALIZED_R24_OR_OUTER_OVERLAP`;
6. otherwise: `RESIDUAL_PEAK_NOT_NARROWLY_LOCALIZED`.

These are **ownership coordinates, not causal wins**. No phase is authorized for production change
merely by receiving a label.

## Next-decision law

- G0–G4 localization -> instrument/ablate the exact G0–G4 parent allocation class; do not revive generic
  subprocess isolation.
- final-verification localization -> isolate verification read/decode lifetime and determine whether
  reusable build-time proof/state can remove duplicated work without weakening strong verification.
- publication localization -> inspect selected/unselected artifact and wrapping lifetime.
- profile-preparation localization -> inspect staged-tree/materialization ownership.
- r24/outer localization -> the topology has materially changed since the old outer-scheduling A/B
  because PrefixGraph now has a proven lifetime boundary; only then may a newly frozen outer A/B be
  considered under this changed composition.
- no narrow localization -> move to heap/allocation ownership rather than further scheduler permutations.

The preregistration, worker, oracle, and workflow are immutable once substantive result-bearing execution
starts. A material correction requires a superseding freeze preserving the old evidence.

# r25 Shifted attempt-5 phase-ownership oracle v1 — result

Status: **TERMINAL / SCOPED NEGATIVE / FORGE R0 / NO PRODUCT OR RELEASE CREDIT**

Frozen preregistration: `docs/v030-rnd/R25_SHIFTED_ATTEMPT5_PHASE_OWNERSHIP_V1_PREREG.md`

Scientific source commit: `a7cae844df17d3043223b78a5d5a10d942775ff1`

GitHub Actions authority:
- run: `33792253583`
- substantive job: `100771395816`
- artifact: `9907851171`
- artifact digest: `sha256:7e22d543bb439f8e3ae3ae14773f13a8b56dd6bcce406087247193d4ec7f29cb`

Decision: **`POST_PLACEMENT_STOPPING_SEAM_RETIRED`**

## Result

Both frozen repetitions were byte-identical, strong-verified to the deterministic Shifted source tree, and measured the post-Placement tail far below the preregistered 0.15 attempt-5-wall feasibility floor.

| rep | attempt-5 total | Placement | Placement fraction | post-Placement tail | tail fraction | residual compile |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 49.472488 s | 49.444034 s | 99.942485% | 0.028454 s | 0.057515% | 0.026910 s |
| 1 | 49.361728 s | 49.340009 s | 99.956002% | 0.021718 s | 0.043998% | 0.020513 s |
| median | **49.417108 s** | **49.392022 s** | — | **0.025086 s** | **0.050756%** | **0.023712 s** |

Archive identity for both repetitions:
- bytes: `1,723,056`
- SHA-256: `791baff9fe09b18588f26bdc47ff1b13f160ca095dff2e47b5523241e85c91e9`
- source/reconstructed tree SHA-256: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`
- `strong_verify_ok=true`
- residual pack selected in both repetitions
- delta auditions: `1,369`
- residual pack records: `9`
- residual-packed delta nodes: `153`

## Causal interpretation

The preregistered seam required at least 15% of attempt-5 wall to remain after Placement even under the deliberately impossible optimistic assumption that every later instruction could be deleted for free. The measured median remaining budget is only **0.050756%**. The seam misses the frozen plausibility floor by roughly **295x**.

Therefore residual compilation, winner publication, or any other intervention beginning only after the attempt-4 Placement builder returns cannot be the primary repair for the current Shifted creation red. Placement itself owns effectively the entire accepted attempt-5 child wall on the tested deterministic Shifted regime.

This is a scoped negative constraint, not universal dogma. It covers the exact inherited attempt-5 path, deterministic Shifted corpus, and current builder family. Reopening the post-Placement seam requires new causal evidence that materially moves work out of Placement or changes the exact release gap; a nearby parameter sweep is insufficient.

## Forge decision

- retire post-Placement / residual-pack stopping as the primary Shifted runtime intervention under this regime;
- preserve PrefixGraph compression and whole-tree RSS wins;
- do not weaken the fresh-process runtime bands or skip G0-G4 heuristically;
- continue the already-frozen nested-stage attribution authority, then place the next exact stopping/admission proof **inside the Placement owner before material edge/delta work** if that authority confirms graph-construction dominance.

No product bytes, benchmark comparator, representation cost, integrity/locality/recovery invariant, or release threshold changed. This result has **zero release credit**.

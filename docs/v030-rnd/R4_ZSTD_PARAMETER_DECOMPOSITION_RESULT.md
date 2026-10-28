# v0.30 R4 Zstd parameter-decomposition result

**Status:** POSITIVE DIAGNOSTIC / WHOLE-ARCHIVE VALIDATION REQUIRED  
**Authority branch:** `agent/v030-authoritative-integration`  
**Diagnostic source head:** `e99c6609e2bca068353f189cf9eef8c57ba3aced`  
**Workflow run:** `34633062437`  
**Artifact:** `10276927693` (`v030-r4-zstd-parameter-decomposition-e99c6609e2bca068353f189cf9eef8c57ba3aced`)  
**Artifact digest:** `sha256:99d1b6a3836d0e469d852f69bbf3b2ce0cbf5bd7f325843541aec2e480b7d0ae`  
**Shipping credit:** none

## Mission lock

The selective-final-effort R4 closed a broad family: on a frozen level-1 representation, an oracle cannot close the accepted v0.29 Office/Analytics floors under ZIP-time constraints simply by promoting a sparse subset of final calls to ordinary Zstd-19. Analytics is particularly diffuse, while Office has insufficient total recoverable bytes.

That result does not imply that every part of the Zstd-19 preset is equally responsible for its density or time cost. Zstd levels bundle several compression parameters. This diagnostic therefore freezes the v0.25 structural representation and asks a narrower causal question:

> Can a strict subset of the level-19 compression parameters recover a material fraction of the level-15 density gap for less than half of level-19's measured incremental final-compression time?

Disproof was explicit: if no non-level19 hybrid recovered at least 50% of the Analytics level-15 -> accepted-v0.29 gap while using at most 50% of the level-19 incremental final-compression time, parameter recombination would be retired as the primary R4 route.

## Contract

No production selector, format, comparator, filesystem semantics, integrity rule or representation-discovery policy changed. The experiment:

- uses the repaired neutral-hostile identities and accepted v0.29 floors;
- preserves sub-final structural/probe behavior;
- explicitly reproduces ordinary Zstd-15 and Zstd-19 presets byte-for-byte from their resolved parameter sets;
- measures each final compression variant twice and round-trips every measured payload;
- predicts complete archive bytes by replacing only final physical payload sizes inside the already-built level-15 artifact;
- strong-verifies and canonically restores the fixed representation before parameter attribution;
- grants no release credit.

## Result

The hypothesis is **supported as a diagnostic**.

### Analytics/database — decisive positive signal

Accepted v0.29 floor: `6,135,172 B`  
Fixed level-15 representation: `6,569,059 B`  
Gap: `433,887 B`

Two hybrids clear the preregistered investigation gate:

| Hybrid | Predicted archive | Gap to v0.29 | Recovered fraction of L15 gap | Final-compress time | Fraction of L19 extra final time |
|---|---:|---:|---:|---:|---:|
| L15 + L19 `strategy` + `searchLog` | **6,218,886 B** | +83,714 B | **80.71%** | 4.2975 s | **46.77%** |
| L15 + L19 `strategy` | 6,251,941 B | +116,769 B | 73.09% | 3.9790 s | **42.67%** |

This is a real decomposition result: most of the useful density movement is not tied to the entire level-19 preset.

The diagnostic also exposes the edge of this family. A more expensive hybrid, L15 + L19 `strategy` + `searchLog` + `targetLength`, predicts `6,134,872 B`, only **300 B smaller** than accepted v0.29, but its measured final-compression time is `7.5337 s`. Ordinary level 19 predicts `6,135,709 B`, still 537 B above v0.29, at `8.4284 s`. Therefore parameter recombination can almost exactly reproduce the inherited density floor, but the cheapest promising point remains materially above it.

### Office workspace

Accepted v0.29 floor: `5,954,026 B`  
Fixed level-15 representation: `6,081,882 B`

The strongest level-19-family points approach but do not beat the inherited floor. The smallest prediction was `5,955,339 B`, still **1,313 B above** v0.29. Ordinary level 19 was `5,955,341 B`, +1,315 B. This is useful hostile evidence: parameter decomposition does not create a magical exact-floor win on every structured workload.

### Developer repository control

Accepted v0.29 floor: `744,337 B`  
Fixed level-15 representation: `838,930 B`

Even the strongest tested parameter combinations remain about `66.8 KiB` above v0.29 (best prediction `811,106 B`). Parameter recombination therefore cannot explain the Developer gap and must not be generalized into a universal v0.30 repair.

## Causal interpretation

The prior negative result remains intact: **selective ordinary high effort on the frozen representation is retired**. This new result changes a different premise. Zstd-19's density/time tradeoff is not monolithic; `strategy` and `searchLog` account for a large fraction of the Analytics density recovery while avoiding more than half of the measured incremental final-compression work.

This does not yet prove a useful product point because the current receipt is a call-level physical prediction over a fixed built representation. It does not include a fresh whole-archive build timing boundary for the hybrids, and prediction bugs or representation interactions remain possible.

## Hostile review

The strongest reasons to reject premature productization are:

1. the promising Analytics hybrids still lose deterministic bytes to accepted v0.29;
2. Office still misses the v0.29 floor even near the strongest tested settings;
3. Developer retains a large gap, so this is not a general density repair;
4. call-level marginal timing is not complete verified creation time;
5. no workload-blind admission rule has been demonstrated;
6. peak RSS, selective-read work and broader all-15 behavior have not been remeasured for a hybrid.

Therefore **no production integration is authorized by this result**.

## Next decisive action

Build the promising parameter hybrids as complete authenticated archives on Office, Analytics and multiple hostile/no-benefit controls. Preserve all sub-19 discovery/probe behavior, require deterministic repeated sizes, strong verification and canonical restore, and compare complete verified creation time against level 15, ordinary level 19 and ZIP on identical input.

Only if the whole-archive result reproduces the causal gain without control regressions should the project design a workload-blind bounded admission rule and then pay the normal all-15, RSS, locality, recovery, native and release-evidence costs.

If whole-archive validation fails, retire parameter recombination as the primary R4 and move to a genuinely different representation/execution primitive rather than adding more parameter sweeps.

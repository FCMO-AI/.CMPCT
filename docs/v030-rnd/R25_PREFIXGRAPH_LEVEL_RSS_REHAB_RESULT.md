# r25 exact PrefixGraph bounded Zstd-level RSS rehabilitation result

Status: **CLOSED / ACCEPTED SCOPED FORGE NEGATIVE / `PREFIXGRAPH_LEVEL_REHAB_INSUFFICIENT` / NO RELEASE CREDIT**

This record closes the frozen experiment in `R25_PREFIXGRAPH_LEVEL_RSS_REHAB_PREREG.md`. The result-bearing execution used exactly the preregistered level ladder `[19, 18, 17, 16, 15]`, target, owner, three-round rotating order, RSS/size/wall budgets, candidate accounting, tree-identity requirement and terminal-decision grammar. No level or threshold was changed after result-bearing execution began.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `0ea22f59822184a6fc62a2cebab75992c867a5f5`
- workflow: `CMPCT v0.30 PrefixGraph bounded level RSS rehabilitation`
- workflow run: `33677624088`
- substantive job: `100406214465` (`level-rss-rehab`)
- artifact id: `9865318910`
- artifact: `v030-prefixgraph-level-rss-rehab-0ea22f59822184a6fc62a2cebab75992c867a5f5`
- artifact digest: `sha256:94e2e27b031f9bfe5d941f5e4a9a47613831623c13b0bcd6ec07736abc196ad4`
- schema: `cmpct-v030-prefixgraph-level-rss-rehab-v1`
- target: `resemblance_hostile_v1 / 01_shifted_versions`
- rounds: `3`
- release credit: `false`

The deep result-bearing job, frozen decision ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully. This is substantive diagnostic evidence, not a classifier-only workflow green.

## Frozen identity and validity gates

All required gates passed:

- exact semantic owner: `experiments._v030_canonical_prefixgraph` through canonical profile-isolation PG;
- source tree SHA-256 at every level: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`;
- selected anchor: `0` at every level;
- anchor auditions: `18` at every level;
- each level deterministic across all three fresh-process repetitions on complete selected archive bytes and SHA-256;
- every repetition strongly verified the identical source tree;
- raw dictionary bytes, all-direct payload compression, anchor nomination, candidate pricing/tie law, grammar and decoder were unchanged.

The experiment intentionally permitted compressor-level-dependent candidate bytes; equality to level 19 was therefore not required. Reconstruction identity and deterministic within-level archive identity were required and passed.

## Exact result

The decisive RSS comparison is median **total fresh-process peak RSS**, as frozen. Incremental RSS is diagnostic only.

| Level | Selected archive | Median total RSS | Median incremental RSS | Median wall | RSS reduction vs L19 | Size delta vs L19 | Wall ratio | Qualified |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 19 | **1,700,242 B** | **200,212 KiB** | **77,016 KiB** | **9.731462 s** | — | — | 1.0000x | no |
| 18 | 1,700,292 B | 199,808 KiB | 76,612 KiB | 9.698176 s | **0.2018%** | +50 B | 0.9966x | no |
| 17 | 1,700,235 B | **198,768 KiB** | **75,572 KiB** | 9.229727 s | **0.7212%** | **-7 B** | 0.9484x | no |
| 16 | **1,700,224 B** | 199,144 KiB | 75,948 KiB | 9.279156 s | **0.5334%** | **-18 B** | 0.9535x | no |
| 15 | 1,700,303 B | 199,232 KiB | 76,036 KiB | **6.467178 s** | **0.4895%** | +61 B | **0.6646x** | no |

Frozen rehabilitation qualification required all of:

1. total-peak RSS reduction >= **15%**;
2. selected archive size penalty <= **8,192 B** and <= **0.50%**;
3. wall ratio <= **1.10x**;
4. deterministic archive and exact strong tree reconstruction.

All lower levels easily satisfied the size and wall budgets, and levels 16/17 were slightly **smaller** than level 19. Level 15 was about **33.5% faster** than level 19 while paying only +61 B. None of those performance facts rehabilitates the targeted RSS owner: the best observed total-RSS reduction was only **0.7212%** at level 17, more than twenty times smaller than the frozen 15% materiality threshold.

## Terminal decision

The frozen terminal decision is:

**`PREFIXGRAPH_LEVEL_REHAB_INSUFFICIENT`**

`selected_rehab_level = null`.

Every preregistered lower level produced <15% total-peak RSS reduction. Compressor level is therefore retired as the **next primary workspace lever** for the exact canonical PrefixGraph owner under this tested Shifted regime. Do not widen the ladder or lower the memory threshold merely because levels 15–17 improve wall time or preserve/nearly preserve bytes.

## Causal interpretation

This negative sharpens the existing CCtx result rather than contradicting it. The exact-owner attribution still shows one live raw-prefix `ZSTD_CCtx` as a material allocation class inside PrefixGraph. What this experiment demonstrates is that the large live workspace is **not materially reduced by moving from Zstd level 19 down through level 15** under the same raw-dictionary PrefixGraph construction path.

The measured memory plateau is striking: L19 median total peak was 200,212 KiB and every lower level remained within about 0.2–0.7% of that value, even though L15 cut wall time by roughly one third. That separates CPU effort from the dominant live-memory footprint in this regime. The next justified question is therefore not another nearby compression level; it is a different implementation/workspace boundary that can supply the required compression semantics without paying the same large live context footprint.

This result is distinct from the historical parameter negatives already preserved in the repository:

- chain-log reductions saved <1% RSS and hash-log reductions worsened RSS materially;
- glibc arena caps saved at most about 8.2% while exporting wall-time debt;
- window-log 22/21 saved <1%, while window 20 catastrophically changed the winning representation and worsened bytes/time/RSS;
- precomputed-CDict increased RSS materially;
- fresh-CCtx-per-member did not lower RSS and more than doubled wall time.

Together, those results make repeated Python-zstandard parameter/lifetime tuning a low-value family unless a material implementation change supplies new causal evidence.

## Release-scale implication

This diagnostic grants zero release credit. The latest substantive promoted-product Shifted authority remains governed by the separate strict runtime/RSS contract and is materially above its `<=1.25x` peak-RSS ceiling. Do not combine ratios from different exact heads/runners as though they were one release measurement.

The bounded level ladder cannot plausibly close that product gap: its largest exact-owner total-RSS movement was <1%. The stronger streaming-finalize mechanism remains worth preserving independently because it previously produced a much larger byte-identical memory reduction, but the complete product still requires a second large causal owner or an intervention that subsumes more of the high-water.

## Forge decision and next action

Retire nearby compressor level as the next primary PrefixGraph RSS lever. The next R3/R4 experiment should target a **different Zstd implementation/workspace boundary** rather than another Python `ZstdCompressor` knob. Candidate directions must first prove that they preserve the required candidate accounting, reconstruction, dictionary semantics and near-byte-equivalence; examples include an isolated native/libzstd construction path or another implementation boundary that can measure workspace ownership directly. A new experiment must be frozen before result-bearing execution and must price carrying cost, portability/native parity and complete-product integration rather than treating an isolated RSS delta as release proof.

## Reopening predicate

Reopen the compressor-level family only if at least one of the following materially changes the causal regime:

1. the zstandard binding/library or compressor implementation changes such that workspace allocation by level is demonstrably different;
2. PrefixGraph changes its compressor construction/dictionary semantics in a separately justified product mechanism;
3. allocator/workspace evidence identifies a level-sensitive allocation class that was not present or observable in this experiment.

Runner noise, a wider post-hoc level sweep, a lower RSS threshold, or the attractive L15 wall-time result alone is not a reopening predicate.

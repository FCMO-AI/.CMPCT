# v0.30 EG08 low-yield work attribution result — 2026-09-13

Status: **causal attribution PASS; research evidence only, no promotion credit**

Exact measured head: `7a47f7c1ae579503ba9cd758d50d35a6772c0437`

Hosted run: `34765374766`

Artifact: `10320081657`

Artifact digest: `sha256:fc6c21ad3320b0bff48940fe0ca78fe0aea8e82cd6e2b6cd359b52c7cbef5ec2`

Scientific verdict: `EG08_LOW_YIELD_REJECTED_WORK_DOMINATES`

## Contract and validity

This attribution was preregistered against the two low-yield rows that had already failed the independent eligible-nine creation-cost gate: neutral `10_large_mixed_binary` and hostile `05_incompressible`. It changed no codec level, pack membership, admission law, locality rule or product byte.

An initial attribution implementation was adversarially rejected before receiving scientific authority because a later byte-identical tie could have been misclassified as the selected rung even though EG08 retains the first strict-best candidate. The authoritative run above includes the repair: only the recorded first strict-best level that exactly equals the final stored frame can receive `final_selected` credit.

The corrected run is valid:

- EG07 and EG08 build-time strong verification PASS on both surfaces;
- locality geometry is identical EG07↔EG08;
- every reconstructed physical pack payload equals the actual EG08 payload exactly;
- reconstructed per-pack savings equal the complete-artifact EG07→EG08 byte delta.

## Aggregate result

Across the two frozen low-yield surfaces:

- effort calls: **576**;
- final-selected calls: **40**;
- superseded/tied calls: **536**;
- never-best rejected calls: `0`;
- measured ladder CPU: **1.520466101 s**;
- measured discarded/superseded CPU: **1.503102887 s**;
- discarded CPU share: **98.86%** aggregate.

The label `rejected-work` in the preregistered verdict vocabulary includes work whose candidate bytes are not present in the final archive; in this result almost all such work is technically `superseded` or storage-tied rather than immediately worse. That distinction matters for the next mechanism: naive first-worse pruning cannot recover this cost because the ladder produced **zero early stops** on both surfaces.

## Large Mixed

`10_large_mixed_binary`:

- complete-artifact saving: **56 B**;
- effort calls: `256`;
- changed packs: `40`;
- final-selected calls: `40`;
- final-selected CPU: **0.017363214 s**;
- superseded/tied calls: `216`;
- superseded/tied CPU: **0.678547671 s**;
- discarded CPU share: **97.50497%**;
- early stops: `0`.

Thus nearly all measured ladder CPU is spent producing frames that are not stored. The tiny 56-byte aggregate gain is not expensive because the 40 winning frames themselves take long; it is expensive because the ladder repeatedly proves that later/equal alternatives do not beat the first selected storage choice.

## Hostile incompressible

`05_incompressible`:

- complete-artifact saving: **0 B**;
- effort calls: `320`;
- changed packs: `0`;
- final-selected calls: `0`;
- superseded/storage-tied calls: `320`;
- superseded/tied CPU: **0.824555216 s**;
- discarded CPU share: **100%**;
- early stops: `0`.

Every measured higher-effort call is proof traffic whose bytes are discarded. Because the candidates tie the RAW stored size rather than becoming strictly worse, EG08's first-worse rule cannot terminate the ladder early.

## Interpretation

The low-yield creation debt is **not an intrinsic cost of the selected EG08 frames** on these two diagnostic surfaces. It is overwhelmingly the cost of proving that alternative effort levels do not produce a better stored choice.

That is strong mechanism-level support for an exact cheap-opportunity / proof-reuse direction. It does **not** justify a workload-name gate, a `<4 KiB` product threshold, or simply stopping after the first tie. Office already supplied a counterexample to the naive `RAW at level 1 => higher effort cannot win` assumption: EG11 recovered one RAW incumbent that higher effort improved by `129,782 B`.

Therefore the next Builder must discriminate opportunity from futility using content/codec evidence while preserving the Office raw-incumbent counterexample and exact product semantics. A gate that merely skips RAW or tie ladders is already falsified by repository evidence.

## Score custody

No Genesis score, composed R4 score, v0.29 comparator, locality ceiling, integrity/recovery semantics, format revision, numeric version or ONE status changes. The result attributes implementation work; it does not earn new density.

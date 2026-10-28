# Office canonical-r25 escape result

Status: **accepted scoped negative research evidence; no release credit**

## Question

Can the current canonical r25 product candidate escape the Office regression by selecting only the shipping Geometry G04 / PrefixGraph candidate set while preserving the existing locality and exact-tree contract?

## Exact evidence

- source commit: `3e6fb03b568bfcce3a75fd9f536dee9688df5a6e`
- workflow: `CMPCT v0.30 Office canonical-r25 escape oracle`
- run: `35332576811`
- job: `105560023933`
- artifact: `10542196652`
- artifact ZIP SHA-256: `5dd375969062c736e574c4e3f906ac0ad6dd414fc93582388a95b53ce8cc6c44`
- substrate: `neutral-hostile-determinism-repair-v6`
- Office tree SHA-256: `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57`
- logical bytes: `16,063,798`
- files: `20`

The oracle selected `geometry-g04`. Strong verification and exact-tree verification passed. Selected-member read amplification was `1.0x`, within the unchanged `<=8x` bound.

## Complete-artifact result

- canonical r25 candidate: **11,633,016 B**
- shipping r24 control: **15,445,236 B**
- current v0.29 floor: **5,954,330 B**
- solid Zstd-19 control: **8,312,879 B**
- 7z control: **7,455,748 B**
- canonical-r25 create time: **90.579031777 s**

Therefore canonical r25 saves **3,812,220 B** versus the shipping r24 control, but loses **5,678,686 B** versus the current v0.29 floor, **3,320,137 B** versus Zstd-19, and **4,177,268 B** versus 7z. The oracle decision is `CANONICAL_R25_ESCAPE_INSUFFICIENT` and `release_credit=false`.

PrefixGraph was not selected: its candidate size was `7,605,401 B`, but its authenticated-metadata locality preflight reached **10.970673170161499x**, violating the unchanged `<=8x` product bound. That is a real product constraint, not a benchmark knob to loosen.

## Interpretation

This kills a tempting local escape route: merely forcing the existing canonical r25 Geometry/PrefixGraph product set cannot replace the much stronger inherited v0.29 Office floor. Geometry G04 is materially better than shipping r24 but still far too large; PrefixGraph is smaller but currently inadmissible on locality and would still be larger than the v0.29 floor even if locality were repaired.

The next Office work should therefore attack the information/ownership mechanism behind the inherited compact floor rather than spend primary effort tuning canonical-r25 selection. In particular, the separate full-charge v0.25 ZIP-stream ablation is the right causal instrument for determining how much of the inherited Office advantage is actually owned by ZIP-stream virtualization. If that value is material, the engineering target becomes a bounded productization/ownership route for that structure; if it is not, this family should be retired and the remaining v0.25 physical owners isolated instead.

## Claim boundary

This is Office-only research/oracle evidence. It does not change canonical release authority, prove all-15 generalization, authorize a format/version change, satisfy competitor gates, or relax locality. The authoritative v0.30 branch remains merge/tag/version/publish locked until the strict release contract is independently satisfied on one exact candidate fingerprint.

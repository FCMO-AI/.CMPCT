# ONE-G0.2 plan-direct V2 writer attribution — terminal result

Date: 2026-09-06

## Decision

`localize_plan_direct_v2_writer_owner`

Primary measured owner: **`segment`**.

The promoted plan-direct V2 compiler changed the writer cost structure enough that the next speed lane should target native segmentation, not the already-rehabilitated serializer or the previously-falsified local nomination microstructure.

## Exact-source authority

- Branch: `research/cmpct1`
- Experimental line: `ONE-G0.2`
- Exact workflow/source head: `002e945dfd9023c15935a7fd6f358ed651bf7700`
- Workflow: `ONE-G0.2 plan-direct V2 writer attribution`
- Run: `34044589633`
- Job: `101517264933`
- Artifact: `9992712377`
- Artifact digest: `sha256:a7f10a8dfb8fcdd4e44448c70bed53e6a9311446bb16faea786caa8e989541f7`
- Full ONE semantic/hostile suite: passed
- Semantic failures: `0`
- Native-plan oracle failures: `0`
- Frozen rounds: `31`

## Instrumentation validity

The attribution itself passed the preregistered overhead gate:

- mature productive profiled/unprofiled median: **`1.0031471710x`**;
- mature productive worst: **`1.0298758525x`**;
- mature control median: **`1.0088379350x`**;
- overhead gate: **pass**.

The timers therefore did not perturb the writer enough to invalidate the ownership result.

## Mature productive phase ownership

| Frozen phase | Median share |
|---|---:|
| native segmentation / plan construction | **35.1295%** |
| plan-direct canonical wire | **23.1265%** |
| root SHA-256 | **16.6041%** |
| relation admission | **1.3435%** |

The remaining difference to 100% is ordinary Python/call/measurement boundary work outside the four explicitly timed interiors; shares above are normalized over the frozen phase medians for owner selection.

Only `segment` clears the frozen material-owner rule: median share `>=25%` and size-median share `>=20%` at at least two mature sizes.

## Stability by mature size

Segmentation share is unusually stable:

| Relation bytes | Median segment share |
|---:|---:|
| 16 KiB | 35.1295% |
| 32 KiB | 35.1103% |
| 64 KiB | 35.4681% |
| 128 KiB | 35.3421% |
| 256 KiB | 34.2741% |

That stability is much stronger causal evidence than a single hot workload. The next optimization lane can therefore attack segmentation without inventing a workload classifier.

Direct-wire share is consistently material but misses the frozen 25% primary-owner threshold: about 26.64%, 23.49%, 22.17%, 21.10%, and 21.73% across the same sizes. It remains a secondary owner, not the next selected target.

Root hashing remains roughly 15.44–17.11%; admission falls from ~2.72% at 16 KiB toward ~1.0% at large sizes and is not a credible near-term speed target.

## Workload shape

The phase split is workload-sensitive in an interpretable way:

- simple `shift_plus1` plans spend relatively more on hashing/direct wire because segmentation yields only a few segments;
- `damage_quarter` raises segmentation sharply;
- `fragmented_every96` raises both segmentation and direct-wire work because it creates dense plan/node structure;
- disabled controls have effectively zero segmentation cost, as expected.

This matches mechanism rather than threshold behavior.

## Semantic/resource truth

This lane changes no ONE representation, reader opcode, canonical bytes, stored size, locality, integrity, recovery or comparator setting. It is attribution only.

The result is bounded to the adjacent-version root-hash-charged plan-direct V2 writer. It does not establish arbitrary/fused-discovery ownership or product-native authority, and it does not compare ONE against v0.29 or deferred v0.30.

## Hostile reviewer

- No phase labels or owner thresholds changed after seeing the result.
- `direct_wire` is not promoted as co-owner merely because it is second; it missed the frozen primary-owner criterion.
- Instrumentation overhead remained within its independent validity gate.
- Exact wire/plan semantics and independent native-plan oracle remained green.

## Next decisive work

Attack the **native one-pass segment-plan constructor** as the next writer speed owner.

First characterize its causal work before changing it: it currently reports one compared target byte per relation byte on productive rows. Build a preregistered native A/B around the exact segment-plan kernel that asks whether equivalent spans can be emitted with less scalar byte traffic / fewer branch transitions, preferably by bulk mismatch/run detection or SIMD-friendly block comparison, while preserving the exact segment plan and Surprise boundaries.

Do not weaken the segment-plan oracle or allow a different-but-equivalent segmentation in the first speed lane: require byte-for-byte plan identity so any speed result isolates implementation work rather than representation policy. If a later policy experiment wants to change segmentation, preregister that separately and charge stored bytes, reader work and locality.

# ONE-G0.2 native fused nomination + mirrored fp8 local view — result

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`
Preregistration: `docs/one/evidence/ONE_G02_NATIVE_FUSED_NOMINATION_FP8_MIRRORED_PREREG_2026-09-06.md`

## Terminal decision

**Reject the mirrored-fp8 sidecar as the fused nomination baseline speed optimization. Preserve it as causal evidence and as a validated exact local-index representation.**

The candidate remains semantically exact, but the strengthened exact-source run fails the preregistered speed law because the hit-rich productive control exceeds the 1.03x row ceiling and the mature productive median misses the <=0.95x promotion threshold.

No threshold, workload membership, semantic requirement, or resource bound was changed after observing the result.

## Exact-source boundary

- fused baseline source blob: `89f25972374c747654ddbf631372929b3f21b970`
- promoted isolated fp8 source blob: `00af27f2025e4be4bad92a2e5705cb7f91680584`
- strengthened source HEAD: `96c881c0c730d61250fb9117ba9ec07141291d76`
- workflow: `.github/workflows/one-g02-native-fused-nomination-fp8.yml`
- authoritative strengthened run: `34039174101`
- job: `101502670134`
- artifact: `9991154338`
- artifact digest: `sha256:34bb3022e0dc777e59f6b1ab73729e0dee45065b1f531faef75ad47768afe71b`

The candidate is mechanically derived from the exact fused source and fails closed if either pinned blob moves. It changes only the local 64-entry ring lookup: the full 64-bit keys remain sole authority; the candidate adds the promoted 128-byte mirrored fp8 view and uses fp8 mismatch only as a negative filter. The global 64->8192 demand-grown index is unchanged.

## Semantic / hostile result

The normal ONE semantic/hostile suite passed before the benchmark.

The separately frozen all-collision key-stream audit also passed:

- 110 local lookup events;
- 96 distinct full keys share the same fp8 value;
- ring capacity 64, therefore 32 evictions are forced before repeats;
- baseline hits = candidate hits = 7;
- baseline full-key checks = candidate full-key checks = 4,883, as expected when fp8 has zero selectivity;
- baseline decision checksum = candidate decision checksum = `6979981098549103469`;
- candidate state delta = +128 B;
- decision: `hostile_fp8_exact`.

Across the integrated byte matrix there were zero fused semantic mismatches and zero independent local-audit failures. Every row charged exactly +128 B.

## Authoritative strengthened performance

Strengthened run `34039174101`:

- mature productive median whole-consumer ratio: **0.9555286862x**;
- preregistered requirement: <=0.95x;
- worst productive row: **1.0713172548x**;
- preregistered ceiling: <=1.03x;
- negative/control median: **0.9849912796x**;
- control requirement: <=1.03x;
- terminal benchmark decision: `reject_fused_fp8_speed`.

The failure is concentrated in the deliberately hit-rich local-reuse family. Mature per-family median ratios were approximately:

- `fragmented_every32`: 0.9471x;
- `damage_quarter`: 0.9535x;
- `fragmented_every96`: 0.9543x;
- `shift_plus1`: 0.9555x;
- `local_hit_rich`: **1.0611x**.

Worst hit-rich rows reached ~1.0713x at 256 KiB. In contrast, miss-heavy families generally remained faster: fp8 quickly eliminates almost all full-key comparisons there. On hit-rich streams the 64-entry ring repeatedly finds an authoritative key, while the extra `memchr`/fp maintenance becomes overhead rather than useful rejection work.

This is mechanism-level evidence: the local ring is a real elapsed owner for miss-heavy traffic, but the mirrored fp8 filter is not a uniformly superior replacement for the current fused workload mix.

## Preliminary run and why it is not terminal authority

Before the explicit forced-collision/wrap Hostile Reviewer audit was bound into the gate, exact-source run `34038982766` on HEAD `7d78b838c4b9d5b2fc35f76d5aa1ad131a6902a4` completed successfully:

- artifact `9991095376`;
- artifact digest `sha256:9033a821cf5e39d721ccc0080001c027fdc7877fbfda24cd9ebcca009631126e`;
- mature productive median: **0.8814622872x**;
- worst productive: **1.0025321052x**;
- control median: **0.9204000913x**;
- zero semantic/local-audit failures;
- +128 B on every row.

That run is preserved as evidence of substantial runner/timing sensitivity and as useful causal data, but it is superseded for promotion by strengthened run `34039174101`. We do not select the faster run after the fact.

## Causal interpretation

The two exact-source runs agree on the important shape even though their absolute ratios differ materially:

1. miss-heavy local lookup benefits from cheap fp8 rejection;
2. hit-rich local reuse gets little or no comparison reduction relative to its useful work and can pay a real sidecar penalty;
3. as input grows, global demand-grown nomination and the rest of the fused observer dilute the local lookup's share of elapsed;
4. therefore the isolated ~0.768x local-index result cannot be promoted directly into a whole-consumer claim.

This is the same discipline learned from witness proof-deferral: removing counted work matters only when that work owns enough wall-clock time.

## Strongest negative / regression debt

The negative is not that fp8 is incorrect. It is that **always-on mirrored fp8 is not uniformly cheap enough** under the frozen fused gate. The strongest observed regression is ~7.13% on a 256 KiB hit-rich row, above the allowed 3% ceiling.

Do not rescue this candidate with a post-hoc file-size threshold, hit-rate threshold, workload classifier, or hidden fallback codec. Any successor must arise from a new causal hypothesis and new preregistration.

## Next falsifier

Profile/attribute the hit-rich local path before choosing a successor. The key question is whether the best universal structure is:

- a branchless/SIMD-friendly full-key scan that makes both misses and short-hit searches cheap, or
- an exact tiny associative structure that can reject misses cheaply without imposing `memchr` overhead on frequent hits.

A successor may exploit the causal distinction only if the gate is fixed before measuring and the representation remains one discovery implementation feeding the same ONE Law + Surprise semantics. No reader-visible mechanism is allowed.

v0.29 and deferred v0.30 remain frozen comparators; this experiment grants no comparator or release claim.

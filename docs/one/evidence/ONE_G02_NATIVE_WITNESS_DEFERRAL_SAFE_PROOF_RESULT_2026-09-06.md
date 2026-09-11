# ONE-G0.2 native witness-deferral + safe-proof A/B — terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Exact CI receipt

- exact source: `41e099e1933ab27960765e1993614a7502df068d`
- workflow run: `34008374091`
- job: `101419645176`
- ONE semantic/hostile suite: **93 passed**
- result artifact: `9981694063`
- artifact ZIP SHA-256: `8725e8b8e779873ba2a9f9bcf4cb44a87da9dd14b4e2592ed5ffaaf821bef800`
- result step conclusion: **failure by frozen gate**
- terminal decision: **REJECT `native_witness_deferral_safe_proof` as a speed optimization at this boundary**

The workflow failure is the scientific result, not infrastructure failure. Exact-head checkout, project installation, and all 93 ONE tests succeeded before the frozen A/B returned a rejecting decision.

## What survived

The reference traffic effect transferred exactly into the native A/B. Aggregate relation-specific traffic was:

- baseline: **4,104,106 B**
- candidate: **698,388 B**
- candidate / baseline: **0.1701681194x**

The candidate therefore eliminated about **83.0%** of the measured relation-specific comparison/read traffic by treating the exact 64-byte witness as an Opportunity Gate and skipping speculative left/right extension before the same safe exact proof.

No false Laws were emitted. The same-pointer, forward-overlap, and backward-overlap probes all selected the conservative safe path and reconstructed exactly. When both arms reached the safe proof, dispatcher path and exact-proof counts agreed.

## Why it is rejected

The traffic reduction did **not** become a material native elapsed reduction:

- productive median candidate / baseline: **0.9936649522x**
- worst productive row: **1.0276159507x**
- frozen promotion requirement: productive median **<= 0.95x**, no productive row **> 1.03x**

Negative-control size medians were also essentially neutral, ranging from about **0.978x to 1.008x**.

This is strong causal evidence that speculative extension is not a dominant CPU owner at the tested selector-trace / event-consumer boundary. Removing many compared bytes from a cold or cheap path is not equivalent to removing meaningful elapsed work.

The correct lesson is therefore not "optimize the extension harder." It is:

> **traffic accounting found avoidable work, but elapsed accounting falsified it as the next speed owner.**

Do not reopen this family merely because the 0.170168x traffic ratio looks dramatic.

## Strict semantic audit finding

The pre-result hostile-review amendment required every frozen non-negative case label to reach an accepted Law in both arms rather than allowing a positive row to vanish from the productive denominator.

That audit exposed seven rows where the shared native nomination boundary did not reach a Law in either arm:

- 4 KiB / seed 7 / `fragmented_every96`
- 4 KiB / seed 7 / `hostile_fixed_bands`
- 4 KiB / seed 29 / `fragmented_every96`
- 4 KiB / seed 53 / `damage_quarter`
- 4 KiB / seed 53 / `fragmented_every96`
- 8 KiB / seed 53 / `fragmented_every96`
- 16 KiB / seed 53 / `fragmented_every96`

These are **upstream nomination/discovery coverage debt**, not evidence that witness-deferral corrupted a relation: both arms share nomination and the strict safe-proof parity list was empty. The speed rejection is independent of this stricter coverage failure because the measured productive median already misses the <=0.95x performance gate by a wide margin.

Future discovery work may investigate those missed opportunities, but it must not revive an always-hot rich certificate family whose carrying cost was already falsified.

## Reopening predicate

Reopen witness-deferral as a speed mechanism only if a materially different upstream writer boundary first demonstrates that speculative extension has become a stable elapsed-time owner, or if eliminating the extension is naturally fused with removal of another proven cost owner. Do not reopen by changing witness length, corpus thresholds, or timing gates.

## Claim boundary

This result is native causal evidence at the selector-trace / event-consumer boundary. Trace generation itself remains outside the timed A/B. It changes no ONE reader operation, wire byte, archive semantics, authentication, placement, or comparator authority.

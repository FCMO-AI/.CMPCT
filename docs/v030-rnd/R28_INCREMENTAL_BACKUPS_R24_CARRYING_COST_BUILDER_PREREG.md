# R28 — Incremental Backups r24 Carrying-Cost Builder Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Authority product substrate: PR #56 product code at `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

Trigger evidence: frozen R27 run `33827368679` on exact head `48b7537468f4ac5fa98f61f83025872acfe7abab`, artifact `9920565922`, measured `release-r24 - genuine-r24 = +52,024 B`, `current-product - release-r24 = 0 B`, and 1.0x selected-member locality for all three arms. R27 terminal decision was `D2_LAWFUL_GENUINE_R24_FLOOR_EXISTS_REQUIRE_CARRYING_COST_BUILDER`.

This is a Forge **D2 / R0 attribution Builder** under S6 product-convergence pressure. It is diagnostic only and grants no release credit.

## Question

Which shipping-r24 policy component exports the measured 52,024-byte Incremental Backups carrying cost relative to genuine r24?

The purpose is to identify the exact cost owner before changing product policy. R28 does not assume that any individual knob is globally removable: each shipping policy was introduced for an evidenced reason, including <=8x selective-read locality and previously promoted strict wins.

## Frozen target and identity

Use only deterministic repaired `neutral_hostile_v1/06_incremental_backups` generated through the current canonical benchmark substrate. Every arm must reconstruct and strongly verify the same product tree. Any identity/correctness mismatch terminates interpretation.

Record the canonical full release fingerprint at execution and bind product immutability by requiring that the checked-out head descend from `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a` with no product/corpus/policy changes after that authority substrate. Only R26/R27/R28 diagnostic/preregistration/workflow custody files may differ.

## Frozen arms

All experimental arms use the same canonical r24 `Builder`; no grammar or reader changes are permitted. Release-policy arms also apply the already-promoted dead-dictionary post-selection elision so that dictionary payload is not confounded with the R28 question.

1. **genuine-r24** — unmodified `cmpct.builder.Builder(source).build()`.
2. **release-r24** — current promoted `entropygraph_v030_release_product._locality_bounded_r24_build()`.
3. **mature-deflate-threshold** — release-r24 policy except `deflate_reuse_min=65536`, the mature r24 default instead of shipping `0`.
4. **mature-pack-target** — release-r24 policy except micro-pack target remains the mature 256 KiB target instead of the shipping `min(2 MiB, 8 * largest regular member)` target.
5. **mature-pack-max-file** — release-r24 policy except micro-pack maximum member size remains the mature 32 KiB instead of shipping 256 KiB.
6. **no-medium-bin-pack** — release-r24 policy except `.bin` is not added to the existing S_PACK admission view.

The shipping single-large-file fixed-8-MiB rule is retained in all release-policy arms. R27's target has multiple regular files, so this factor is expected to be inactive; the instrument must record source shape rather than infer inactivity from the workload name.

## Frozen measurements

For each arm record:

- complete archive bytes and SHA-256;
- exact product-tree SHA-256 and strong verification;
- archive format revision/profile;
- build wall time and fresh-process peak RSS;
- selected largest regular member;
- operation-derived decoded-context bytes and read amplification;
- effective deflate threshold, micro-pack target, micro-pack max-file, medium-binary admission and wide-single-file state.

For every experimental arm compute:

- `bytes_vs_release = arm_bytes - release_r24_bytes`;
- `bytes_vs_genuine = arm_bytes - genuine_r24_bytes`;
- fraction of the 52,024-byte positive gap removed when applicable.

Hard locality ceiling remains **<=8.0x**. R28 may not call a smaller artifact useful if it violates that ceiling.

## Frozen interpretation law

- **SINGLE_OWNER** — exactly one one-factor arm restores `<= genuine-r24` bytes, remains correct, and stays <=8x. That factor becomes the leading D2 carrying-cost owner, but product change still requires a superseding global Builder that proves the policy can be made conditional/elided without losing the positive workloads that originally justified it.
- **MULTIPLE_SINGLE_OWNERS** — more than one one-factor arm independently restores the floor. Do not pick the most convenient knob; next Builder must compare global carrying cost and retained positive evidence.
- **PARTIAL_OWNER** — no one-factor arm restores the floor, but at least one removes a positive material fraction of the 52,024-byte gap. Follow with a preregistered interaction/conditional-elision Builder; do not assume additivity.
- **NO_ONE_FACTOR_EXPLANATION** — none of the frozen factors reduces the positive gap. Preserve the negative result and inspect remaining D2 ownership/interaction rather than tuning thresholds.
- **LOCALITY_DEBT** — any byte-restoring arm exceeds 8x. That arm is not a lawful fallback and cannot be promoted.
- **SUBSTRATE_OR_CORRECTNESS_FAILURE** — product/corpus drift, identity mismatch, missing accounting or failed strong verification. No scientific interpretation.

## Strongest simpler controls and alternatives

- Revert all shipping-r24 policy to genuine r24: rejected as a product intervention because it would throw away previously evidenced locality/strict wins and would not identify carrying cost.
- Add a third complete genuine-r24 build to the product tournament: explicitly forbidden by R27 because it buys bytes with global create/RSS cost.
- Workload-name/path dispatch: forbidden.
- Representation invention: premature; R27 proved a lawful byte/locality floor already exists inside r24.

## Success handoff

A successful R28 identifies a concrete D2 owner or interaction with exact bytes. The next experiment must test a **content-derived, generic conditional/elision rule** across the R28 target and the policy's protected positive/adversarial workloads, including create time, RSS, locality and exact bytes. Only that later Builder can authorize a product edit.

## Anti-cheating / immutability

After first result-bearing execution this document, target, arms, constants, 8x ceiling, identity law and interpretation law are immutable. A material change requires a new superseding freeze. No release threshold, comparator, corpus identity, locality rule, recovery/integrity guarantee, benchmark semantics or product selector may be weakened to manufacture green status.

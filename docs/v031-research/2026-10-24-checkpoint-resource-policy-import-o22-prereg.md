# O22 — Shared resource-policy isolation for signed Reader cold opens (preregistration)

**Status: FROZEN BEFORE CODE.** UTC 2026-10-24. Source-exact parent: PR #365, `54c998200b1908b696ade049fe94df71a736c284` (released v0.30.0 / physical revision 24 unchanged). Independent causal economics owner: PR #371 O13.

## Baseline / observed debt
O13 [run 40118135703](https://github.com/FCMO-AI/.CMPCT/actions/runs/40118135703) source-only O9 → O10R (same synthetic authentic r24 archives) measured signed checkpoint import+constructor 29.294 → 32.090 ms (512) and 34.757 → 36.486 ms (4096). Gross subprocess checkpoints 86.638 → 92.439 ms (+5.801 ms / 6.70%) and 96.097 → 99.149 ms (+3.052 ms / 3.18%). Security caps are indispensable: O10R [negative 40109918111](https://github.com/FCMO-AI/.CMPCT/actions/runs/40109918111) fails before patch; [positive 40110160739](https://github.com/FCMO-AI/.CMPCT/actions/runs/40110160739) passes on three hosts. O13 absolute cost attribution to `validation` import is a hypothesis; Python startup noise or imported transitive modules may contribute.

## Question, prediction, falsifier
Can Reader retain **the same exact `ParserLimits` policy object, environment mapping, error class identity and fail-closed authenticated-generation/depth gates**, but avoid eagerly importing the much heavier strict structural validation module for signed **checkpoint-only** opens? Prediction: a tiny shared `resource_policy` module avoids `cmpct.validation` import on ordinary signed-checkpoint Reader initialization while preserving strict-validation API compatibility; checkpoint median cold import+open declines measurably versus the actual O10R parent. Exact product improvement is **unmeasured** until real same-runner A/B.

Falsify/narrow if: (1) the Reader still imports `cmpct.validation` on the checkpoint path; (2) existing O10R authenticated compressed size/depth adversaries cease rejecting or exception class identities differ; (3) `preflight_archive` behavior/env/defaults diverge; (4) valid journal replay, extraction or archive identity changes; (5) the full-product cost is neutral or worse under repeat same-runner evaluation. An apparent speedup from weaker checks is a LOSS, not a win.

## Alternatives and BONK
A. Leave eager strict-validator import: safe but retains measured O13 checkpoint cold debt.
B. Duplicate the ParserLimits constants in Reader: cheapest import but divergent hard limits; rejected.
C. Import entire strict validator only after the parsed generation has already consumed bytes: risks ungated decompression; rejected.
D. Split shared `ValidationError`/`ResourceLimitError`/`ParserLimits` into a tiny module, re-export from `validation`, and import this in signed generation checking; keep `_apply_delta` lazy for actual journal replay. This is the smallest semantics-preserving viable mechanism. No new on-disk fields, parser thresholds, comparators or release criteria.

## Evidence ladder and cost contract
Before promoting product credit: use source-exact inherited O10R focused adversarial tests, new independent class-identity and checkpoint-no-strong-validator-import test, full CI/platform package as available. Then run an honest **same-runner** alternated fresh-process O10R vs O22 cold Reader A/B (512 and 4096 signed journal AND checkpoint) with repeat raw subprocess wall, operation CPU, peak RSS, identical physical archive SHA/tree and environment. Startup and import must be included separately; native/package and official create/extract parity must not be inferred from micro evidence. Old and new code/source blobs must be pinned, not hand-recreated.

## Coordination and limits
PR #365 owns the signed-generation security fix, PR #371 owns original cold economics; O22 is a new narrow optimization claim on an independent branch stacked on exact #365. Do not modify their branches. Current unmerged PR pileup and late same-file edits mandate review before downstream integration. Stronger future full source/IO/destination guarantees remain separate. No merge, version change, format change or release authorization. This prereg does **not** assert a win.

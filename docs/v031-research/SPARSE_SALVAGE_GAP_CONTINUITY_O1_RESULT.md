# CMPCT v0.31 sparse disjoint-extent continuity O1 — decisive result (2026-10-23)

**Classification: SCIENTIFIC HYPOTHESIS FALSIFIED; prior standalone reenactment not source-faithful. No product defect established.** Parent [PR #296](https://github.com/FCMO-AI/.CMPCT/pull/296) original oracle script blob `94fc2234df0035938be3151dfaa5eef7bc317598`; incumbent scanner blob `94c25029fdd167c00871aabbe8fe90fbe7490026`. Independently preregistered O1 at commit `98a4d45b66ed0e943b4572f953bd8cbe1e8ae1ee`; failure-expecting instrument committed `fdb8d82a4562d1b0b0f14b644e29f7b11d9705b1`.

## Exact-source hosted observation

Workflow [40040863477](https://github.com/FCMO-AI/.CMPCT/actions/runs/40040863477) executed on `31d9f79e8932926f7574ded1cb3804507fb9d456`. The source-hash/HEAD checks and installation of the unchanged real CMPCT package succeeded. The scientific step raised the frozen failure-expecting assertion:

```
AssertionError: ('falsifier not reproduced or parent oracle changed',
                 [4194432], [4194432])
```

The old product bounded scanner **and** the O0 sparse oracle returned the single valid third-extent record at 4,194,432. The hypothesis predicted an additional phantom at B−3, 2,097,149; that candidate was **absent**. The CI workflow's red state reflects the falsification of the preregistered hypothesis, *not* an external-infrastructure failure, product test regression, or proof of a real parity defect.

## Causal reinspection and correction

The earlier local standalone simulation incorrectly carried magic-suffix state between `SEEK_DATA` extents. The exact source had already implemented the correct rule: `carry=b""` is assigned **inside the outer per-extent loop** immediately after `pos=start`; only adjacent chunk reads within that extent carry suffix bytes. Therefore the simulation's false candidate was an artifact of its own altered semantics, not evidence against the actual oracle.

This is a negative result: **the proposed extent-carry-reset repair is unnecessary**. The absence of an explicit `header[:4] == BMAGIC` check also does not independently prove a defect under a static filesystem, because every found `scan.find(BMAGIC)` corresponds to real adjacent bytes within one extent. More extensive hostile/source-mutation cases remain unmeasured, not silently passed.

## Scientific decision and reusable next action

1. Retire the claim that PR #296 has a proven cross-hole split-magic false positive.
2. Preserve the three layout variants as **regression controls of existing correct behavior**, if their actual extents and baseline semantics remain checked. A follow-up test may assert positive parity but cannot be relabeled a confirmation of the failed hypothesis.
3. No fix to the source oracle, scanner, product, format, admission or release gates is warranted from O1.
4. Counterfactual: reading `pos=start; carry=b""` with accurate indentation before designing the reenactment would have killed this question in seconds. More general lesson: when source implementation can already answer a mechanistic hypothesis, source inspection is the cheapest control and beats a creative but unfaithful independent model. **No discovery-policy edit is earned from this single process failure.**

Owner [PR #296](https://github.com/FCMO-AI/.CMPCT/pull/296) was informed in a follow-up correction; the initial unsupported warning was explicitly withdrawn. This research retains complete prediction and contradiction history.

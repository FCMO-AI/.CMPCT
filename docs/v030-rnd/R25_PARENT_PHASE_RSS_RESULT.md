# r25 parent-phase RSS attribution result

Status: **accepted Forge R0 causal localization / no release credit**

This record closes `docs/v030-rnd/R25_PARENT_PHASE_RSS_PREREG.md` on the exact result-bearing source. It is an ownership coordinate, not a release receipt and not permission to alter product scheduling by itself.

## Authority

- exact source head: `2cf15ca8af71909d05563bd1104370005d1bbb5d`
- workflow: `CMPCT v0.30 parent-phase RSS attribution`
- workflow run: `33615847760`
- substantive job: `100201353867` (`parent-phase-rss`), completed success
- artifact: `v030-r25-parent-phase-rss-2cf15ca8af71909d05563bd1104370005d1bbb5d`
- artifact id: `9841000524`
- artifact ZIP SHA-256: `9848286f64293622225e951a5d8122515901984460ff7180e831da14dd85959d`
- schema: `cmpct-v030-r25-parent-phase-rss-v1`
- experiment valid: **true**
- repetitions: **3** fresh processes
- release credit: **false**

The exact-head substantive job, identity ratchet and CI-topology self-check all passed. This is not a classifier-only success.

## Exact result

Frozen target: `resemblance_hostile_v1 / 01_shifted_versions` under the accepted diagnostic topology where exact PrefixGraph runs in one disposable child and exits, while exact G0–G4 remains in the parent.

All repetitions emitted the same canonical selected product:

- selected: `prefixgraph`
- format revision: `25`
- complete bytes: **1,700,603 B**
- physical SHA-256: `4d0c71d74c9de8f35fed2fa0bc29c5193674e380d804d220f4c05dc51a31c03d`
- genuine r24 product price: **30,275,597 B**
- repaired-source canonical filesystem tree: `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16`

| repetition | whole-tree peak RSS | parent `ru_maxrss` | wall time | peak phase signature | samples |
|---|---:|---:|---:|---|---:|
| 1 | **290,056 KiB** | 289,724 KiB | 67.660 s | `r24-build + r25-build` | 6,237 |
| 2 | **289,372 KiB** | 288,996 KiB | 68.252 s | `r24-build + r25-build` | 6,309 |
| 3 | **289,320 KiB** | 289,176 KiB | 68.714 s | `r24-build + r25-build` | 6,310 |

Median whole-process-tree peak: **289,372 KiB**. Median parent `ru_maxrss`: **289,176 KiB**. Median wall time: **68.2521 s**. The sampled global high-water had only **one process alive** in all three repetitions.

The phase decomposition is also stable. Representative repetition 1 peaks were:

- `r24-build + r25-build`: **290,056 KiB**;
- `g04-build + r25-build`: **231,144 KiB**;
- `final-verify`: **194,084 KiB**;
- `r25-build` without the r24 consume seam: **142,348 KiB**;
- `profile-prepare`: **43,720 KiB**.

Across all repetitions the G0–G4 phase peak was roughly **224–231 MiB**, materially below the ~289 MiB global peak.

## Frozen decision

**`RESIDUAL_PEAK_LOCALIZED_R24_OR_OUTER_OVERLAP`**

Every global-peak signature contained `r24-build`; none contained `g04-build`. This satisfies the exact preregistered localization rule.

## Causal interpretation

The changed topology matters. The accepted predecessor already showed that disposing PrefixGraph's process lifetime before later work reduced honest whole-tree peak RSS from **400,958 KiB to 289,300 KiB (-27.8478%)**, while exporting substantial create-time debt. The subsequent dual-isolation A/B showed that disposing G0–G4 as well changes the remaining peak by only **38 KiB (0.0131%)**.

This phase result now shows that the remaining high-water is created earlier, while the canonical r24-consume seam is waiting on the already-started r24 prebuild and r25 construction is also live. It therefore provides the new causal evidence required to reopen an **outer-overlap question under this changed product composition**.

It does **not** erase the earlier outer-scheduling negative. That old A/B tested unchanged shipping topology and, by contract, left the release-product r24 prebuild executor untouched. Its 9.9863% result remains valid for that regime. The new evidence authorizes a different question: after PrefixGraph lifetime isolation, does removing the actual r24-prebuild/r25 overlap collapse the newly localized ~289 MiB peak?

## Scoped constraints

1. Do not attribute the residual peak primarily to G0–G4 merely because G0–G4 still runs in the parent.
2. Do not rerun the old `cmpct-v030-product` executor serialization and call it a new test; it intentionally leaves the prebuild overlap untouched.
3. Do not weaken the RSS gate or sacrifice the selected PrefixGraph byte gain.
4. Any next A/B must preserve exact genuine-r24 construction and pricing, exact r25 candidate semantics, selected output bytes/tree, PrefixGraph's accepted diagnostic process boundary, recovery/integrity/locality laws, and all release thresholds.

## Next decisive action

Freeze and execute a changed-topology A/B with two otherwise identical PrefixGraph-isolated arms:

- control: inherited r24 prebuild overlaps later r25 work;
- barrier: the same exact r24 prebuild is required to finish after profile preparation and before r25 candidate work proceeds, while its completed artifact remains consumed through the unchanged canonical r24 pricing seam.

This directly tests the owner localized here. Charge honest whole-process-tree peak RSS and wall time. A material memory win must keep its runtime debt visible and still earns no release credit until productized and passed through the full runtime/platform authority.

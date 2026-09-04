# r25 genuine-r24 process-lifetime RSS result

Status: **ACCEPTED DIAGNOSTIC CAUSAL EVIDENCE / FORGE-CUSTODY / NO RELEASE CREDIT**

This record preserves the result of the frozen `R25_R24_PROCESS_LIFETIME_RSS_PREREG.md` experiment. It is a scoped causal result for the Shifted runtime/RSS red. It changes no production scheduler, representation, selector/admission rule, archive grammar, benchmark threshold, locality/decode-unit bound, integrity/recovery requirement, or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact experiment source: `36322daf7c5915a2246c35a6e9ecebd28828896a`
- workflow run: `33624563734`
- substantive job: `100230166805` (`process-lifetime-rss`)
- artifact id: `9844677128`
- artifact: `v030-r25-r24-process-lifetime-rss-36322daf7c5915a2246c35a6e9ecebd28828896a`
- artifact digest: `sha256:6b0070c0d2df73d92d5a0a319ca6489c50e5f84aa789d32f0cc0f3118f94adf7`
- schema: `cmpct-v030-r25-r24-process-lifetime-rss-v1`
- experiment valid: `true`
- worker failures: `0`
- release credit: `false`

The substantive measurement, frozen-contract ratchet, CI-topology custody check, and artifact upload all completed successfully. The decision below comes from the result-bearing job rather than a classifier-only workflow status.

## Exact identity

Every row reconstructed the same repaired Shifted tree and emitted the same selected product:

- target: `resemblance_hostile_v1 / 01_shifted_versions`
- accepted historical source tree: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`
- product tree: `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16`
- selected representation: `prefixgraph`
- format revision: `25`
- selected complete archive: `1,700,603 B`
- selected archive SHA-256: `10dfaf5ea4cfac5e8dcb6eeafd0c853766042b9d094322ab90814fa6bed49eb1`
- charged genuine-r24 complete bytes in this instrument: `30,275,591 B`
- charged r25 complete bytes: `1,700,603 B`

The semantic-owner identity ratchet passed for exact canonical PrefixGraph, G0-G4 and release-reader owners. All wrappers were restored, child processes returned successfully, and the <=10 ms whole-process-tree sampler recorded no errors.

## Result

The preregistered decisive metric is sampled **whole-process-tree RSS**, not parent-only `ru_maxrss`.

| Arm | Median whole-tree peak RSS | Median wall time | Change vs inherited peak |
|---|---:|---:|---:|
| inherited canonical overlap | **400,338 KiB** | **36.4474 s** | baseline |
| same-parent serialized control | **567,014 KiB** | **34.2261 s** | **41.6338% worse** |
| r24-child serialized | **583,342 KiB** | **34.7570 s** | **45.7124% worse** |

The lifetime-specific comparison is also negative: terminating the genuine-r24 child before r25 begins is **2.87965% worse** than the matched same-parent serialized control in whole-tree peak RSS. The r24 child exited successfully in both repetitions; its own reported peak `ru_maxrss` was 225,596 / 225,024 KiB.

The child-isolated arm was modestly faster than inherited on wall time (`0.953622x`), but this experiment is an RSS attribution test and that timing observation does not rescue the memory hypothesis or grant product-speed credit.

## Frozen terminal decision

**`R24_PROCESS_LIFETIME_RETIRED_AS_PRIMARY`**

The frozen support condition required both >=20% total peak reduction versus inherited and >=10% lifetime-specific reduction versus the same-parent serialized control. The frozen retirement condition was total reduction <10% or lifetime-specific reduction <5%. Instead of reducing either quantity, child isolation increased both.

Therefore, under this exact Shifted regime, **allocator/native pages retained solely because the genuine-r24 builder remains in the same process are not the primary explanation for the shipping r25 RSS high-water**.

## Scoped causal interpretation

This result closes the generic “move genuine r24 into a short-lived child and the Shifted RSS red disappears” intervention. It must not be reopened merely because parent-only `ru_maxrss` looks lower in one arm: the frozen instrument deliberately measures the whole process tree, and process isolation introduces concurrent/delegated child memory that parent-only accounting would hide.

The result does **not** prove that the genuine-r24 builder has no memory cost, nor that process isolation can never be useful for another workload or architecture. It says its lifetime retention is not the dominant cause of the current Shifted product high-water under this exact canonical composition.

A reopening predicate requires new causal evidence that materially changes the tested ownership regime—for example, a product design that avoids the delegated-process overlap charged here while preserving exact output and demonstrating >=20% whole-tree reduction. Repackaging the same work behind a subprocess boundary is not new evidence.

## Forge implication

The causal chain has now retired profile capture, exact candidate-family ownership in isolation, inner candidate serialization, outer r24/r25 serialization as the primary explanation, generic GC/allocator trimming as a high-water rescue, G0-G4 process isolation, the r24-prebuild barrier, and genuine-r24 process-lifetime isolation.

The next Shifted RSS experiment should therefore stop permuting scheduling/process boundaries and move to **allocation/lifetime attribution inside the complete r25 candidate/product build itself**. It should identify a concrete live or temporary allocation class large enough to explain a material fraction of the ~400 MiB inherited peak before any Builder intervention. Whole-process-tree accounting, exact selected bytes/tree, and no-release-credit status remain required.

Strongest self-critique: the experiment shows where **not** to intervene, but it has not yet lowered shipping RSS. Its value is narrowing the remaining causal search space without sacrificing the PrefixGraph size win or weakening the release gate.

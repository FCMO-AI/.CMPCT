# r25 PrefixGraph process-isolation RSS A/B v2 result

Status: **accepted Forge R2 causal evidence / material RSS intervention with major create debt / no release credit**

This record preserves the result of the superseding custody freeze `R25_CANDIDATE_PROCESS_ISOLATION_RSS_V2_PREREG.md`. V2 reused the V1 scientific instruments unchanged and repaired only evidence custody. The result therefore answers the original frozen question without rewriting the experiment after observation.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact source head: `95d8e8a059ede1d9c5804c50ab1e0903703db40b`;
- workflow: `CMPCT v0.30 candidate process-isolation RSS A/B v2`;
- workflow run: `33613317989`;
- substantive job: `100193333773` (`candidate-process-isolation-rss-v2`);
- artifact: `v030-r25-candidate-process-isolation-rss-v2-95d8e8a059ede1d9c5804c50ab1e0903703db40b`;
- artifact id: `9840029576`;
- artifact ZIP digest: `sha256:4fe57eac65a7fae5b8d9307c4bb9637bdded5c04e96a7ef45337bd49d6effa35`;
- schema: `cmpct-v030-r25-candidate-process-isolation-rss-v1`;
- experiment valid: `true`;
- worker failures: 0;
- release credit: false.

The job checked out the exact source SHA, executed the unchanged frozen worker/oracle, passed the frozen identity/decision ratchet, explicitly passed `tools/check_ci_topology.py` on the V2 workflow, and uploaded the exact JSON receipt. This is substantive evidence, not a classifier-only success.

V1 remains preserved historically. Its scientific measurement was valid but its workflow lacked the repository's required deep-lane/exact-receipt topology and its topology self-check accidentally supplied no workflow path. V1 is therefore not used as authority here. V2 independently reproduces the same causal direction under valid custody.

## Exact result

| arm | median whole-process-tree peak RSS | median parent `ru_maxrss` | median wall time | median sampler count |
|---|---:|---:|---:|---:|
| shipping control | **400,958 KiB** | 400,616 KiB | **35.7111 s** | 3,302 |
| PrefixGraph isolated then G0–G4 | **289,300 KiB** | 288,972 KiB | **42.1324 s** | 3,925 |

Frozen derived quantities:

- whole-process-tree peak reduction: **27.8478%**;
- wall-time ratio: **1.179814x** (**+17.9814%**);
- frozen decision: **`PROCESS_LIFETIME_BOUNDARY_SUPPORTED_WITH_MAJOR_CREATE_DEBT`**.

Every repetition charged the parent plus all transitive live descendants at <=10 ms sampling, collected far more than the frozen >=100 samples, reported no sampler errors, and preserved exact semantic-owner identities. Parent-only `ru_maxrss` was diagnostic only and did not determine the result.

Both arms preserved the same complete selected product identity: same selected representation, same archive bytes and physical SHA-256, same canonical filesystem user-tree verification, same r24/r25 complete-product prices and same format revision. The isolated arm intercepted exactly one canonical PrefixGraph submission, executed it in one fresh Python child, received successful exact-owner stats, and observed that child exit before continuing G0–G4. No production source was changed.

## Causal interpretation

This is the first material positive intervention in the Shifted RSS causal chain after several scoped negatives.

The result demonstrates that **process lifetime itself owns a large fraction of the shipping Shifted high-water**. Generic same-process `gc.collect()` and `malloc_trim(0)` could not lower peak RSS, even though allocator trim returned ~154 MiB of live pages after PrefixGraph. Moving that exact PrefixGraph build behind a true process-lifetime boundary lowers the honestly charged whole-system peak by **111,658 KiB** at the median.

That is not an accounting trick: the frozen metric sums parent and all live descendants. The process boundary changes lifetime, not representation bytes. The fact that the maximum sampled process-tree peak occurs with only one process alive does not negate child charging; it means the decisive high-water occurs after or outside the child's lifetime. The intervention prevents the child's allocation history from remaining part of the parent process when later work creates its own peak.

The result also exposes significant exported debt. The isolated arm is **17.98% slower** to create under this same-runner diagnostic. That crosses the frozen >15% major-create-debt boundary. Therefore this evidence supports process lifetime as a causal memory lever but does **not** justify shipping the subprocess architecture as-is.

## Relation to the causal chain

Accepted predecessor evidence now supports the following narrow model:

1. canonical profile/manifest capture alone is not the dominant RSS owner;
2. exact PrefixGraph and exact G0–G4 in isolation do not individually reproduce shipping peak;
3. serializing the two candidates in the same process does not improve peak and can worsen it;
4. serializing outer r24/r25 product work lowers peak by only ~9.99%, below its primary-owner boundary;
5. pre-candidate retained state is below its 10% primary-owner boundary;
6. generic same-process GC/allocator reclamation cannot lower peak;
7. **disposing PrefixGraph's entire process lifetime before later candidate work lowers honest whole-tree peak by 27.85%.**

The evidence therefore shifts the Forge from generic scheduler/reclaim tuning to **candidate lifetime architecture**.

## Scoped claim and non-claims

Supported claim: on the exact repaired Shifted workload and exact canonical r25 semantic owners, a true process-lifetime boundary around PrefixGraph materially reduces whole-system peak RSS while preserving exact product bytes and semantics.

Not supported:

- that subprocess isolation is release-ready;
- that the current 289,300 KiB peak satisfies the frozen release RSS gate;
- that the same architecture helps ML, where PrefixGraph is structurally ineligible;
- that the wall-time cost is acceptable;
- that Linux `/proc` sampling or Python subprocess routing is a portable production implementation;
- any release credit.

## Strongest self-critique

The result is large but incomplete. It converts one part of the Shifted memory problem into a proven systems lever, yet the isolated arm still peaks around **289 MiB** and pays nearly **18% create-time debt**. Merely shipping this intervention would rehabilitate one metric while worsening another frozen release blocker. It may also introduce portability/startup/process-management carrying cost across Windows, Android and constrained hosts.

The next experiment must therefore ask whether the remaining ~289 MiB is another separable candidate lifetime rather than immediately productizing this design.

## Forge decision and next decisive experiment

**Advance the process-lifetime hypothesis one bounded R2 step, but do not promote it.**

The next decisive Shifted experiment is dual candidate process isolation under the same honest charging law:

- execute exact PrefixGraph in a disposable child and wait for exit;
- execute exact G0–G4 in a separate disposable child and wait for exit;
- retain only the minimal exact stats/artifact files needed for canonical winner selection/publication in the parent;
- charge parent + all live descendants as the decisive system peak;
- require byte-identical final archive/tree/selection and unchanged r24/r25 prices;
- expose wall time and process-start carrying cost;
- grant no release credit.

If isolating G0–G4 after PrefixGraph materially reduces the remaining ~289 MiB peak, candidate lifetime architecture becomes a stronger rehabilitation path whose next challenge is recovering concurrency/startup cost without reintroducing memory overlap. If it does not, the remaining owner lies inside G0–G4 or parent publication/verification state and the Forge should stop adding process boundaries.

Separately, ML extraction/runtime remains its own causal lane and must not inherit this Shifted result.

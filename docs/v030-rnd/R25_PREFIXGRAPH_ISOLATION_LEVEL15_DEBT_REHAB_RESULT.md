# r25 PrefixGraph process-isolation + level-15 debt rehabilitation result

Status: **ACCEPTED FORGE REHABILITATION WIN / `ISOLATION_LEVEL15_DEBT_REHAB_SUPPORTED` / NO RELEASE CREDIT**

This record closes the frozen experiment in `R25_PREFIXGRAPH_ISOLATION_LEVEL15_DEBT_REHAB_PREREG.md`. It combines exactly two previously measured facts without reopening either family: the large whole-process-tree RSS benefit of the exact PrefixGraph process-lifetime boundary, and level 15 only as payment for that boundary's exported create-time debt. No threshold, corpus, accounting rule, process topology, candidate grammar or interpretation changed after result-bearing execution.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `ee6a50b32699aa3f35d510e1a498ae8addb553da`
- workflow: `CMPCT v0.30 PrefixGraph isolation level-15 debt rehabilitation`
- workflow run: `33679301272`
- substantive job: `100414722236`
- artifact id: `9866453440`
- artifact: `v030-prefixgraph-isolation-level15-debt-ee6a50b32699aa3f35d510e1a498ae8addb553da`
- artifact digest: `sha256:2bbacaf4b611bae8d971eade322e053eb50b356b26346baffe4b46f5bdde1a8e`
- schema: `cmpct-v030-prefixgraph-isolation-level15-debt-rehab-v1`
- target: `resemblance_hostile_v1/01_shifted_versions`
- experiment valid: **true**
- release credit: **false**

The result-bearing A/B/C, exact identity/lifecycle ratchet, frozen-budget ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully.

## Exact result

Each arm ran twice in rotating order. The decisive memory metric was sampled live **parent + all transitive descendants** at <=10 ms intervals; every row had thousands of samples and no sampler errors. Parent-only `ru_maxrss` remained diagnostic.

| Arm | Final archive | Median whole-tree peak RSS | Median wall |
|---|---:|---:|---:|
| shipping PrefixGraph level 19 | **1,700,604 B** | **366,056 KiB** | **66.487692 s** |
| isolated PrefixGraph level 19 | **1,700,604 B** | **257,252 KiB** | **72.247017 s** |
| isolated PrefixGraph level 15 | **1,700,667 B** | **257,758 KiB** | **68.607845 s** |

The shipping and isolated-level-19 controls were exact on selected representation, complete archive bytes, physical SHA-256, r24 product bytes, r25 product bytes, format revision and canonical user tree. The level-15 candidate was deterministic across both repetitions and strongly reconstructed the exact same canonical user tree while retaining PrefixGraph as the final winner.

Frozen derived metrics for `isolated-l15` versus shipping:

- whole-process-tree peak-RSS reduction: **29.5850908%**;
- wall-time ratio: **1.031887907x** — only **3.1888%** slower than shipping;
- wall-time ratio versus isolated level 19: **0.949628766x** — **5.0371% faster**, satisfying the frozen >=5% debt-payment requirement;
- final selected archive penalty: **+63 B**;
- final selected archive penalty ratio: **0.0037046%**;
- r24 product bytes in all arms: **29,883,732 B**;
- candidate byte budget: **pass**.

Frozen qualification required all of:

1. >=20% whole-tree RSS reduction;
2. <=1.10x wall versus shipping;
3. <=0.95x wall versus isolated level 19;
4. <=8,192 B and <=0.50% final size penalty;
5. deterministic exact-tree reconstruction;
6. exact process/isolation semantic-owner and lifecycle gates.

**Every gate passed.**

## Terminal decision

**`ISOLATION_LEVEL15_DEBT_REHAB_SUPPORTED`**

The earlier process-lifetime mechanism is successfully rehabilitated as a credible productization seed. Level 15 is not a memory mechanism—the bounded level ladder already falsified that interpretation. Its role here is narrower and now evidenced: it pays almost all of the process-isolation create-time debt while retaining the large whole-tree memory benefit.

Relative to the predecessor isolated-level-19 result, the same-runner combined candidate cuts the isolation wall debt enough to move from a >15% major-debt regime to only ~3.2% over shipping, while preserving ~29.6% whole-tree RSS reduction. This is the exact rehabilitation objective the preregistration set before execution.

## Strongest surviving critique

This is still **not release closure**. The strict Shifted product authority before this experiment measured r25 peak RSS at `2.9603316534x` genuine r24 against the unchanged `<=1.25x` ceiling, implying about **57.775%** same-semantics reduction merely to reach the release gate on that exact fingerprint. A ~29.6% diagnostic whole-tree reduction is large and actionable, but cannot be mechanically multiplied with results from different exact heads/runners or presented as sufficient release evidence.

The candidate also intentionally changes PrefixGraph's raw-prefix compressor from level 19 to level 15, producing +63 B in this Shifted artifact. That debt is tiny and within the frozen rehabilitation budget, but a production candidate must still satisfy every complete size/product no-regression requirement across the full frozen matrix. Process isolation also exports real platform/carrying cost: subprocess startup, IPC/temp-file lifecycle, failure cleanup, Windows spawn semantics, Android/constrained-host feasibility, native/platform integration and hostile-input/resource behavior all remain unpaid.

## Forge decision

**Advance exactly this combined mechanism to Builder -> Hostile Reviewer at the current complete-product boundary.**

Do not widen the compression-level search and do not retune the process launcher. The next experiment/productization step must use one fixed mechanism equivalent to this winner:

- canonical PrefixGraph construction in a bounded disposable process;
- child completion/exit before the parent proceeds with the remaining tournament lifetime;
- PrefixGraph raw-prefix dictionary compressor fixed at level 15;
- unchanged direct payload compression, dictionary bytes, anchor nomination, candidate accounting, tie law, reader, locality, integrity and recovery semantics.

That single mechanism must then re-earn the ordinary exact complete-product size, runtime/RSS, locality, recovery/integrity, native/platform and release authorities. Any production implementation must fail closed and prove bounded temp/IPC/process cleanup; it may not gift child memory or process startup time.

If exact promoted-product evidence does not retain a material RSS improvement or violates a strict size/runtime/platform row, preserve that result and attack the exported debt rather than weakening the frozen gate.

## Release state

No merge, tag, version bump or publication is authorized by this result. v0.30 remains governed exclusively by the exact-candidate strict release authority.

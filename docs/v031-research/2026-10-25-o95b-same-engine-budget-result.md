# O95b — Same installed O86 engine, same source, budget-only causal attribution

**Date:** 2026-10-25 UTC. **Decision:** `BUDGET_IS_CAUSAL_OWNER_ON_TESTED_FAMILY`. This is independently preregistered research with genuine product execution, not release approval.

## Prospectively locked question and source
- The O95b hypothesis at immutable `70c5bc83cef11f21974222457873f4534f51caec` preceded O95b's instrument, workflow and outcome.
- Genuine Ubuntu 24.04 [Actions #40215554611](https://github.com/FCMO-AI/.CMPCT/actions/runs/40215554611) at exact instrument HEAD `20ce022debeafde76fc1c1b13eccac66eacf1815` **SUCCESS**, six installed source-exact O86 child processes, 3 per arm, zero failed or skipped scientific processes.
- Original raw [artifact #12607128971](https://github.com/FCMO-AI/.CMPCT/actions/runs/40215554611/artifacts/12607128971) with ZIP SHA-256 `14a7440e90450be52cef65c502653f0374f2fdc22180d25f18092ca3a94117c9`. Raw JSON, logs, exact code and source SHA identities reside there.
- Exactly one product source installed for **both** arms: original O86 `6225e30f3e21c0783aa56726b52a3a3583540f99`; Builder Git blob `e46c8670c11c386925f9ae228b25de44c8045f2e`, codec `7d4c4a5a5f00c42561043611e5d4400dd8af38e6`, original O88 fixture generator `2acd2d9ea862b9f018bf1838f89dd2efa3807971`. This is not an O63 vs O86 cross-source comparison.

## Decisive A/B

Both arms build the **same original O88 65 MiB shared three-ZIP source bytes**, with only a public opt-in VZIP exploration-budget environment variable changed. The default arm does not define `CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES` (64 MiB default); the control arm defines it as `134217728` (128 MiB). Three independent child runs per arm; alternating order. Exact ZIP SHA/source integrity, output SHA deterministic per arm, genuine Builder/Reader verify/read/extract and installed code origin all passed.

| Direct product metric (median, same installed O86) | Default 64 MiB | Research control 128 MiB |
| --- | ---: | ---: |
| Representation selected | **S_BLOB** | **S_VZIP** |
| Complete CMPCT archive | **52,641 B** | **664,428 B** |
| Builder CPU | **8.824 ms** | **1,338.635 ms** |
| Independent child VmHWM after Builder | **31,944 KiB** | **304,588 KiB** |
| **Memory difference** | Reference | **+272,644 KiB** |
| Reader verify/read/extract exact | PASS | PASS |

**Primary prediction: confirmed.** Merely raising the budget from 64 MiB to 128 MiB, on the same product executable and identical physical ZIP input, restored VZIP and the roughly 300 MiB child high-water. This near-matches original O95's cross-engine O63 304,756 KiB vs O86 default 32,120 KiB [run #40214780817](https://github.com/FCMO-AI/.CMPCT/actions/runs/40214780817).

The source-composition alternative explanation is thus strongly narrowed: on this case **the budget admission decision itself causes the divergent product memory, complete bytes and CPU behavior**. The budget is not globally optimal, and the 128 MiB arm was a scientific intervention only, not a recommended default.

## Negative knowledge and adversarial scope
- Exactly one structured, highly compressible 65 MiB-shared ZIP family was toggled. This does **not** prove an absolute-budget rule cannot discard more valuable VZIP opportunities in other structures. O71's positive VZIP oracle remains valid.
- Whole-process Linux `VmHWM` is not a function-level allocated-bytes profiler. The contrast is causal for toggling the budget on this exact installed engine and source, not a global allocation attribution law. Actual resident memory can fall after create even though the high-water persists.
- Other system metrics (temporary I/O, selective read amplification, portability, Windows/macOS memory, total release performance) remain unmeasured. The official release gate and frozen performance tests were neither modified nor substituted.
- Preregistered stronger control was justified by O95's discovery that per-child `ru_maxrss` and `VmHWM` disagree. No process/discovery policy modified or rewrite of negative historical O88/O92 evidence was made.
- **Product code changes: none; format revision 24 unchanged; release/merge credit: zero.**

## Decision transfer
O86 owner #444 should use this exact same-engine causal result in convergence economics, alongside O88's original source-exact byte/CPU comparisons and O95's two original 18-child Linux memory trials. The next highest-value unclaimed action is to probe an independent above-budget VZIP-positive held-out family where the admission bound might harm size; if such a family proves large positive opportunity, productize bounded selective admission rather than raising the global budget from this fixture. No new threshold is justified by this experiment.

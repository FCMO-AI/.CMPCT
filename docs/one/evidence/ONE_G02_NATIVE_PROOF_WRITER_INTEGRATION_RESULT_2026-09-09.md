# ONE-G0.2 native exact-proof writer integration result — 2026-09-09

## Decision

**ADVANCE_NATIVE_PROOF_WRITER_INTEGRATION**

The promoted sparse-native-seed V4 writer keeps its exact nomination, generic Program, wire, fallback and reader semantics while replacing the Python exact relation-span proof with the independently-oracled native bulk proof. The result is a large causal writer-speed improvement on productive relation rows without weakening no-op controls or increasing semantic proof traffic.

This is a writer implementation promotion only. It does **not** close the known reader reconstruction/materialization debt of generic relation Programs, does not add a reader-visible operation, and does not move the Genesis supersession gate.

## Exact authority

- branch: `research/cmpct1`
- exact source: `9ca098505845f8831fd0e394a69aefce4ea3f25f`
- experimental state: `ONE-G0.2`
- workflow: `cmpct1-one-g02-native-proof-writer-integration`
- run: `34355087800`
- artifact: `10105371048`
- artifact digest: `sha256:91bf73802c274f661667dd668a69bcd4d2dbfa8b0c4762766c26dcd9645cea56`
- retained JSON: `one_g02_native_proof_writer_integration.json`
- decision emitted by frozen falsifier: `ADVANCE_NATIVE_PROOF_WRITER_INTEGRATION`

The workflow completed successfully after exact-source checkout, frozen-law binding, inherited semantic/adversarial tests, the full integration falsifier, and fail-closed artifact retention.

The integration lane had been introduced with its workflow in the same source push and did not yield the dedicated hosted push evidence needed for adjudication. Source `9ca098...` changes only the workflow comment to re-arm that already-frozen lane; benchmark code, thresholds, candidate mechanism and preregistered scientific law are unchanged.

## Mission lock

Hypothesis: replacing V4's Python exact span proof with the native bulk exact proof should preserve byte-identical V4 representation/coverage and no-op behavior while materially reducing full productive writer CPU. The native proof may read at most `1.01x` the semantic proof span per input.

Frozen decisive gates include:

- every novel row semantically exact and byte-identical to V4;
- novel wire saving >=25% versus the promoted incumbent;
- median novel marginal yield >=20 Mbit eliminated / additional CPU-s;
- median novel CPU <=0.60x V4 and every novel row <=0.80x V4;
- median control CPU <=1.10x V4 and every control row <=1.25x V4;
- incumbent control limits remain <=1.35x median and <=1.75x every row;
- physical proof-load amplification <=1.01x;
- relation state <=0.60x combined input;
- positive probe traffic <=0.09375x combined input;
- no sketch/probe evidence authorizes storage without exact proof.

## Measured result

Across all novel rows:

- median native/V4 CPU: **0.102211x**;
- worst native/V4 CPU: **0.131707x**;
- median native/V4 wall: **0.102192x**;
- worst native/V4 wall: **0.132024x**;
- median marginal yield: **865.067 Mbit eliminated / additional CPU-s**;
- worst observed physical proof-load amplification: **1.000000x**.

Thus the full productive writer path is roughly **9.8x faster than V4 median** after substituting the native proof, while preserving V4 wire and Law coverage exactly.

At 1 MiB combined input (`512 KiB` previous + `512 KiB` current):

| family | incumbent wire | native ONE wire | wire saving | native/V4 CPU | marginal yield | native exact proof |
|---|---:|---:|---:|---:|---:|---:|
| add8 versioned | 1,048,697 B | 524,430 B | 49.9922% | 0.086642x | 954.94 Mbit/s | 2.873 ms |
| XOR versioned | 1,048,697 B | 524,430 B | 49.9922% | 0.097369x | 940.77 Mbit/s | 2.884 ms |
| add8 sparse cracks | 1,048,697 B | 524,656 B | 49.9707% | 0.089879x | 934.18 Mbit/s | 2.882 ms |
| XOR sparse cracks | 1,048,697 B | 524,656 B | 49.9707% | 0.099470x | 921.99 Mbit/s | 2.918 ms |

For those 1 MiB positive rows the gate is ~0.097 ms and sparse seed transfer ~1.15–1.17 ms, so exact proof is no longer a ~45–50 ms Python bottleneck. It remains a meaningful stage, but the full writer now spends only a few milliseconds proving a 512 KiB relation.

### No-op/control economics

Controls continue to reject the relation path before proof/program emission:

- median control native/incumbent CPU: **1.113228x**;
- worst control native/incumbent CPU: **1.209269x**;
- median control native/V4 CPU: **0.995681x**;
- worst control native/V4 CPU: **1.036346x**.

So the native proof substitution does not reopen V2's catastrophic no-op carrying cost. Random, compressed-like, exact-repeat and deliberate probe-false-positive controls preserve incumbent wire and perform zero native exact-proof work.

The mature `+1` temporal case likewise retains incumbent selection and wire; it does not get replaced merely because the generic relation path exists.

## Representation and traffic truth

The new writer remains byte-identical to V4 on every row. At 1 MiB:

- exact relations accept `524,288` relation bytes;
- sparse-crack relations accept `524,280` relation bytes;
- positive relation probe traffic remains `0.09375x` combined input;
- controls remain at `0.046875x` gate traffic;
- modeled relation state remains `0.06640625x` combined input on the 1 MiB positive rows;
- native physical proof loads equal the semantic compared span per input (`1.0x` amplification).

No new reader opcode, hidden codec, fallback, integrity exception, locality exception or recovery exception is introduced.

## Hostile review / strongest remaining debt

The result does **not** make the generic relation path system-complete.

1. **Reader reconstruction debt remains.** At 1 MiB exact relation rows, the generic candidate still models about `1,572,864 B` materialized and `5,242,880 B` reconstruction work; sparse cracks remain worse (`2,097,152 B` materialized / `6,291,432 B` work). Density and writer speed have improved sharply, but reader work still needs a common reconstruction-engine solution rather than relation-specific reader hacks.

2. **Novel rows still cost ~5.5x the narrow incumbent writer CPU.** This is no longer a V4/Python-proof problem—the native candidate is ~0.10x V4—but it means the remaining fixed work (root hashing/incumbent pass, gate, seed transfer, generic Program construction/validation/emission) still needs to earn its place on broader real workloads. The correct next question is not another add8/XOR micro-optimization.

3. **Discovery is still partly duplicated.** The promoted temporal incumbent and generic relation gate remain separate writer-side discovery paths even though both compile into ONE. The eventual ONE architecture should converge toward one fused block observation record and one bounded economic Law-admission budget.

4. **CI trigger debt remains.** Re-arming this one evidence lane still woke nine push workflows. Historical branch/PR fan-out remains compute waste and should be hardened independently without altering scientific comparators.

## Comparison / campaign status

Frozen comparator authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

This ADVANCE is mechanism-level evidence only. It does not substitute for, pre-empt, or weaken the required same-input/same-semantics 15-workload Genesis evaluation at or after the first activation on 2026-09-11.

## Next decisive action

Stop optimizing isolated exact add8/XOR proof. The decisive research direction is now to **fuse the already-promoted sparse relation evidence into the writer's common 64-byte observation record and economic admission budget**, then charge the complete writer on hostile mixed workloads.

A valid next candidate should preserve the current native-proof economics while reducing duplicated observation/state and making expensive Law pursuit depend on expected removable information per expected verification+synthesis cost. It should attack random/incompressible, compressed/media-like, tiny, exact-reuse, sparse-crack, shifted/late relation, structured mixed and multi-version temporal inputs.

In parallel, reader work/materialization should be attacked at the generic reconstruction-engine boundary (cone scheduling/fusion/bulk kernels), not with relation-specific reader modes.

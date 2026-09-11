# ONE-G0.2 exact stage-owner + Crystallization result

Date: 2026-09-08
Exact evidence source: `9fdc3131ff8bf207ee992ae859f532cfd8cae7ad`
Hosted run: `34207064364`
Artifact: `one-g02-native-writer-stage-owner-9fdc3131ff8bf207ee992ae859f532cfd8cae7ad`
Artifact digest: `sha256:97e1f9b055451868261b554cb9f8423c49184c49bff06cc04ba4f64cffff29f5`

## Evidence integrity

The workflow checked out `EVIDENCE_HEAD`, asserted `git rev-parse HEAD == EVIDENCE_HEAD`, provisioned the repository test contract, passed the reachability gate, passed the native observer / owner adjudication / bounded pooling / IR fan-in / range suites, executed all three scientific benchmarks, and uploaded the exact-head JSON artifact.

This is source-head evidence, not a synthetic PR merge-ref result.

## Result A — bounded Surprise pooling advances under the strengthened resource contract

Decision: `ADVANCE_BOUNDED_SURPRISE_POOLING`.

All gates passed:

- exact semantics;
- hard node/ref resource limits;
- unchanged Surprise payload on the frozen productive matrix;
- legacy 1 MiB fragmentation overflow reproduced;
- pooled hostile Program valid;
- 4 KiB selective range cone <=2.1x work/materialization;
- new over-fan-in hostile control selectively Crystallized and round-tripped exactly.

The fine-fragment control used an 8,192-byte every-byte alternating plan with discovered group fan-in 8,192 against the reader cap of 4,096. The compiler Crystallized one 8,192-byte group, emitted no oversized reference node, reconstructed exactly, and produced a 16,501-byte canonical wire for the two-root research Program.

Interpretation: node-count pooling was necessary but not sufficient. With the compiler fallback plus the generic IR fan-in check, an in-memory valid Program can no longer rely on a control vector that the canonical reader rejects.

## Result B — no pre-hard-cap density crossover at 50% reuse on the frozen sweep

Decision: `NO_PRE_HARD_CAP_CROSSOVER_ON_MATRIX`.

Every row was semantically exact. Among rows that did not invoke the hard safety fallback, retaining the discovered 50%-reuse Law remained strictly smaller on canonical wire than Crystallizing the whole current root.

The closest rows were deliberately near the cliff:

- 64 KiB, 9-byte alternating spans: retained Law was 914 bytes smaller than full current-root Crystallization;
- 256 KiB, 9-byte alternating spans: retained Law was 884 bytes smaller.

At 64 KiB / 9-byte spans the retained representation used 31,976 control+integrity bytes and 7,285 encoded refs while saving only 914 total wire bytes versus Crystallization. At 256 KiB / 9-byte spans it used 130,313 control+integrity bytes and 29,143 encoded refs while saving only 884 bytes.

The 8-byte rows crossed the hard fan-in safety boundary and therefore correctly did **not** count as an economic pre-cap crossover.

Interpretation: on this fixed 50%-reuse synthetic family, the canonical density optimum is strikingly close to the hard representability cliff, but still on the Law-retention side. This does not establish that 50% reuse is universally worth retaining: reader work doubles for full current-root reconstruction in the retained rows, and lower reuse fractions may cross economically much earlier.

## Result C — native observation is the repeated 1 MiB whole-writer stage owner

Decision: `OWNER_NATIVE_OBSERVE`.

Frozen owner rule: >=20% median wall share on at least two 1 MiB rows. Native observation cleared it on four 1 MiB rows; native segmentation cleared it on two; Program construction on one. The adjudicator selected native observation from the qualifying stages by median share across the 1 MiB population.

Representative exact-source 1 MiB rows:

| case | composed wall median | native observe | root hash | segmentation | Program construction | emission |
|---|---:|---:|---:|---:|---:|---:|
| shift_plus1 | 8.998 ms | 74.1% | 14.7% | 7.4% | 1.5% | 1.4% |
| shift_plus1_damage_quarter | 19.179 ms | 33.0% | 6.9% | 31.7% | 17.0% | 7.5% |
| fragmented_every96 | 74.696 ms | 8.0% | 1.8% | 20.2% | 43.9% | 16.3% |
| fragmented_every32 control | 7.497 ms | 77.7% | 17.6% | 0% | 0.1% | 3.6% |
| independent_random control | 8.895 ms | 78.1% | 17.5% | 0% | 0.1% | 4.0% |

All semantic and native-plan oracle gates passed.

### Timing-audit caution

The stage-sum/composed audit was near 1.00 on the productive rows shown above except the independent-random control, where stage-sum/composed wall was about 0.8485. The owner decision uses normalized instrumented stage shares, not composed-path fractions. Therefore the owner result is good enough to choose an attribution experiment, but it should **not** be read as a claim that 78.1% of end-to-end random-case wall time is eliminable.

## Hostile-review conclusion

`OWNER_NATIVE_OBSERVE` names a timing region, not yet the C loop. Current `observe_native()` includes:

1. worst-case `_CRun`/`_CReuse` result-array allocation and zeroing;
2. an immutable-bytes `from_buffer_copy`;
3. the C kernel, including its internal index `calloc/free`;
4. Python `Observation` materialization.

The next experiment is therefore the preregistered native-observer boundary-cost decomposition. Optimizing the C scan before measuring those pieces would violate the marginal-information-per-compute discipline.

## Comparator boundary

None of these results earns a v0.29/v0.30 scoreboard point. Stored representation semantics and the reader grammar are unchanged except for stricter rejection of previously wire-undecodable over-fan-in IR. Frozen comparator authorities remain unchanged and the September 11 full same-input gate remains mandatory.
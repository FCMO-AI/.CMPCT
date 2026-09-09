# ONE-G0.2 Relation Writer Envelope V2 — Result (2026-09-09)

Status: **HOLD_RELATION_WRITER_ENVELOPE_V2**

## Mission lock

This experiment tested whether the promoted generic ONE relation path remains economically attractive when charged against the actual promoted root-hash-charged temporal writer rather than a weakened literal-only baseline. The candidate pays the incumbent path first, then adds the shared 64-byte relation witness path, exact maximal-span proof, generic ONE Program construction, full validation, and direct canonical emission. Final wire is the minimum of incumbent and generic representation; reader semantics are unchanged.

The frozen law was not moved after evidence.

## Exact authority

- source SHA: `4204a7e81f977ccc2b775d8b759ae3f02e3d2d0d`
- workflow run: `34340337982`
- job: `102429384792`
- artifact: `10099599677`
- artifact name: `one-g02-relation-writer-envelope-v2-4204a7e81f977ccc2b775d8b759ae3f02e3d2d0d`
- artifact digest: `sha256:c0d755ea6df9f68ec0662406f6aae214e94dd9b1ed7126e033e1a0dac4475384`
- exact checkout / frozen-law binding: PASS
- inherited semantic/adversarial tests: PASS
- frozen falsifier: HOLD

The earlier V1 lineage ending at `5b563809703ede8721fbed1aa5e0864acc56cd8b` remains scientifically inadmissible because it compared against a literal-only baseline weaker than the promoted incumbent.

## Frozen gates

- exact semantics and root equality: mandatory
- novel-relation canonical wire improvement versus incumbent: at least 25%
- median novel marginal yield: at least 20 Mbit eliminated per additional CPU-second
- median control candidate/incumbent CPU: at most 1.35x
- every individual control CPU ratio: at most 1.75x
- false-nomination exact proof: at most 8,192 bytes
- relation probes: at most 0.05x source bytes
- modeled retained relation state: at most 0.60x input
- charged forward source scan: exactly 1.0x

## Result

Semantics, density, proof containment, scan accounting, probe traffic, state ceiling, and novel marginal yield all passed. The always-on writer carrying cost failed decisively.

Aggregate evidence:

- semantic gates: PASS
- median novel marginal yield: **44.99254687311046 Mbit/additional CPU-s** — PASS
- median control CPU ratio: **28.960058558951165x** — FAIL versus 1.35x
- worst control CPU ratio: **31.572263381732167x** — FAIL versus 1.75x
- probe/source ratio: **0.046875x** — PASS
- charged source scan: **1.0x** — PASS
- deliberate false relation nominations: rejected after about **64–65 exact byte comparisons**, far below 8,192 — PASS

Representative 1 MiB two-version rows:

| family | incumbent wire | candidate wire | wire ratio | incumbent CPU | candidate CPU | CPU ratio | marginal yield |
|---|---:|---:|---:|---:|---:|---:|---:|
| add8 | 1,048,697 | 524,430 | 0.500077715x | ~0.960 ms | ~98.102 ms | ~102.14x | ~43.175 Mbit/s |
| xor | 1,048,697 | 524,430 | 0.500077715x | ~0.936 ms | ~87.252 ms | ~93.18x | ~48.591 Mbit/s |
| add8 sparse cracks | 1,048,697 | 524,656 | 0.500293221x | ~0.983 ms | ~99.820 ms | ~101.52x | ~42.417 Mbit/s |
| xor sparse cracks | 1,048,697 | 524,656 | 0.500293221x | ~0.958 ms | ~92.206 ms | ~96.23x | ~45.944 Mbit/s |

Representative control CPU ratios:

- 64 KiB: exact-repeat ~20.13x; random ~22.38x; compressed-like ~20.09x; deliberate probe false-positive ~22.79x; mature +1 preservation ~15.13x
- 256 KiB: exact-repeat ~28.88x; random ~30.03x; compressed-like ~29.00x; deliberate false-positive ~29.27x; mature +1 ~21.87x
- 1 MiB: exact-repeat ~31.57x; random ~31.53x; compressed-like ~28.92x; deliberate false-positive ~30.67x; mature +1 ~22.57x

Reader/access geometry is also not yet a win. At 1 MiB, exact add8/xor candidate materialization is about 1,572,864 bytes versus incumbent 1,048,576, while reader work is about 5,242,880 versus 3,145,728. Sparse-crack rows rise to about 2,097,152 materialized bytes and 6,291,432 reader-work bytes.

## Causal interpretation

The density signal is real: novel predictive relations still cut canonical wire to approximately one half of the promoted incumbent on the strongest versioned cases. The HOLD is caused by creation economics, not by a failed representation principle and not by runaway exact proof on false nominations.

The current V2 candidate invokes the Python `observe_relation_witnesses(...)` path on every input after paying the incumbent writer. Therefore all controls pay a second relation-discovery scan plus Python witness bookkeeping even when no useful relation exists. The magnitude and scaling of the no-op tax make this always-on boundary the primary rehabilitation target. This receipt does **not** claim that witness observation alone owns every measured cycle; the next falsifier must meter the stages independently.

The result does not authorize threshold relaxation. A ~0.50x wire win on favorable inputs does not justify a ~29x median tax on inputs that should have been rejected cheaply.

## Reopening class

Reopen only through a causal writer-cost reduction while retaining the V2 semantic, density, proof, scan, state, and control gates.

The preferred next candidate is **opportunity-gated relation writing**:

1. retain the promoted native triplet block sketch at the already-paid 64-byte fingerprint cadence as the cheap nomination gate;
2. invoke Python/actionable witness geometry and exact maximal-span proof only after that gate predicts a credible non-zero relation opportunity;
3. retain the exact promoted incumbent and final-wire fallback;
4. meter incumbent, gate, witness construction, exact proof/growth, Program construction/validation, and emission independently;
5. falsify on random, compressed-like, exact-repeat, mature +1, probe-false-positive, sparse-crack, late/phase-shifted and novel-relation cases.

Required disproof conditions include any required-relation miss, cross-family alias, false nomination that defeats the proof budget, control median CPU >1.35x, any control >1.75x, or loss of the frozen novel density/yield gates.

## Decision

**HOLD_RELATION_WRITER_ENVELOPE_V2.**

Preserve the representation/density result. Reject the always-on relation-writer carrying cost. Rehabilitate through cheap opportunity gating and stage-level cost ownership, not by weakening the comparator or thresholds.

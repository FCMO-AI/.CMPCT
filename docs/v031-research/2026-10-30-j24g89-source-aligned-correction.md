# J24G89 — methodological correction and preregistered decision boundary

Date: 2026-10-30 UTC. **CORRECTION, NOT A NEW HYPOTHESIS.** Preregistration `c5c243a1621fb75d25cfaeed28bda5d881938c23` and its <10% / 10–20% / >=20% frozen decision ranges remain unchanged. Product/format/release credit **zero**.

## Independently caught fault in the first local instrument

First local 151-sample witness + alternate-seed 151-sample replication incorrectly decompressed and MessagePack-unpacked the primary header's **base compressed index** and then separately decompressed the original complete signed generation-0 checkpoint footer. That duplicated O(N) work in the denominator. It caused an artificially low 5.0–5.4% apparent fraction for one-pass DELETE application and a premature `REPLAY_WORK_LOW_FRACTION_O0` label.

**Source-derived counterexample:** authentic `src/cmpct/reader.py` at #823 `347a62b443bf7c880ed2b86af5d8be7159ee2480` lines 72–121: `_index_from_footer` follows signed predecessors and decodes the first `kind==0` checkpoint **once**, then applies deltas; `_load_index` reads the primary header metadata, but does **not** decompress the primary index while a valid latest footer exists. Our initial two-decode method was not a fair model of that path. The first faulty script remains recoverable at Git parent `b226d07b15ed6f15c471b5c727a735399cec62d9`; **do not cite its optimistic number as a finding**.

## Corrected source-aligned methodology

On the **same original physical J24G83 bytes**, retain independent validation of primary header/index digest and all 65 linked authentic footers before timing. Within each timed one-pass pass, decode/authenticate the signed generation-0 full checkpoint **once**, then independently decode/authenticate generations 1–63; build one 63-member DELETE set and filter a newly decoded private index once; construct the same name lookup dictionary. The reader's signed-history file search and physical I/O remain outside these local in-memory timings, so the result is a **research O0 stage ceiling**, not a source-exact Reader benchmark.

Second Github-source code commit `195a77436a0b581b2683fc0014a8baf5809ec89a` makes exactly that correction to `research/j24g89_replay_headroom.py`. Earlier raw local data are preserved, not rewritten.

## Corrected independent local observations (not yet hosted)

Two separate 151-sample, seed/order-differentiated local iterations on the same authentic source SHA256 `5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a` (8,192/middle) and `8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81` (32,768/tail):

| Real family | Corrected replay wall fraction, first/replication | Whole-process-independent staged wall, first/replication | Generous replay-free speed ceiling |
|---|---:|---:|---:|
| 8,192 / middle | **10.130% / 10.492%** | **4.969ms / 4.479ms** | **1.1127× / 1.1172×** |
| 32,768 / tail | **9.881% / 10.348%** | **20.124ms / 18.602ms** | **1.1096× / 1.1154×** |

**Revised decision from the exact original preregistration: `AMBIGUOUS_10_TO_20_PERCENT`.** H1 `<10% on both` did **not** survive both independent replications. Do not retire checkpointing on the original rejected 5% fraction, and do not promote checkpointing on a ~10% threshold-crossing isolated O0 result. Another format/policy change would incur full bytes, identity, recovery, decoder and portability cost.

Signed 63-delta payload authentication/decode contributes only approximately 0.09–0.10ms in these local trials; the prior ~5–19ms attributed to that stage was mostly the duplicate full checkpoint decoding. Thus even the previously attractive "skip footer work" intuition is unsupported by the corrected source-aligned local instrument.

## Self-review, next decision and coordination

This correction is an **actual method failure caught by reading executable Reader code**, not a variant tuned to force a result. Source-exact installed #823 `OwnedCMPCT` reconstruction and three-host repeated timing are stronger comparators and remain independently owned. The hosted J24G89 workflow must be evaluated on the new code SHA; earlier queued work on its parent is superseded but must remain visible as evidence. No schema, evaluator, prereg, release law, benchmark, `docs/discovery/STATE.json` or other agent's code was weakened. In particular #574 owns shared discovery state, #823/#820 own Reader and #842 owns ordinal representation.

**Prospective transferable lesson candidate (not policy adopted):** in any performance falsifier, confirm source-exact decoder control flow and ensure each shared physical decoding stage is charged once before attributing a fractional bottleneck. A single correction does not justify modifying the Discovery Engine normative policy.

Next independent decision, if exact source/product owner wants it: source-exact A/B within the owned Reader measuring incremental saved work from a hypothetical provable checkpoint at generation32 **while retaining full signed safety and recovery**; no inference from this independent Python O0 alone.

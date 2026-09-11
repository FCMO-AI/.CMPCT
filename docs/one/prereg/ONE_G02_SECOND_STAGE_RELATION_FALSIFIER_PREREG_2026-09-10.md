# ONE-G0.2 second-stage relation falsifier preregistration — 2026-09-10

## Mission lock

Test whether a second, deterministic, sparse and **disjoint** observation set can cheaply kill ADD8/XOR candidates that collide with the current frozen 16-point nomination sampler, while preserving true relations and retaining full exact proof as the only authority allowed to accept a Law.

This is a transfer-only discovery-efficiency experiment. It does not execute Genesis inputs, does not change reader semantics, and does not authorize a product threshold.

## Baseline

The current ONE-G0.2 general writer nominates ADD8/XOR from 16 deterministic sample positions. An economically admissible candidate that matches those positions proceeds to an exact full relation proof. For a same-length relation of `N` bytes, that proof accounts for `2N` source+target bytes.

Hosted sampler-collision evidence already established that an adversarial near-miss can satisfy all 16 nomination samples yet force the complete proof before being rejected. The 4096-byte hostile rows therefore pay 8192 proof bytes while correctly emitting Surprise.

## Falsifiable hypothesis

A second observation set formed only from positions not used by the frozen primary sampler can reject a one-byte near-miss placed on that second set with far less source+target traffic than the avoided `2N` exact proof, without rejecting true ADD8/XOR relations.

The experiment must also preserve a stronger adversary: a one-byte corruption placed outside **both** sparse sets must survive both stages and reach the unchanged exact proof, where it must be rejected. This dual-collision row quantifies the unavoidable overhead of an additional sparse stage when sparse evidence is insufficient.

## Frozen geometry

Primary sampler authority for this experiment is independently transcribed as 16 equidistant integer positions over `[0, N-1]`, matching the currently frozen writer contract. The benchmark must assert writer `_sample_positions(N)` equals this independent transcription.

Second-stage positions are independently defined as follows:

1. Take every adjacent pair `(a, b)` in the independently derived primary positions.
2. Compute `m = a + (b - a) // 2`.
3. Keep `m` only when `a < m < b` and `m` is not a primary position.
4. Preserve sorted unique positions.

No writer helper may define the oracle second-stage geometry. If a later implementation uses a different geometry, that is a new experiment.

Frozen lengths: `32, 256, 4096, 16384` bytes.

Relations: `ADD8(+37)` and `XOR(0xA5)`.

For every relation/length pair construct three deterministic rows:

- `true`: exact relation across the whole target;
- `stage2_collision`: exact relation except one byte poisoned at the first second-stage position;
- `dual_collision`: exact relation except one byte poisoned at the first position outside the union of primary and second-stage positions.

If a frozen length cannot provide the required second-stage and dual-collision positions, the experiment fails closed rather than silently changing the matrix.

## Cost model

Only source+target bytes inspected for relation checking are counted here.

For candidates that already passed the primary sampler:

- baseline remaining work = `2N` exact-proof bytes;
- candidate remaining work = `2K + 2N` when the second stage survives, where `K` is the number of second-stage positions;
- candidate remaining work = `2K` when the second stage rejects.

The benchmark must not count the already-paid primary sampler in one arm but not the other.

## Gates

H1 — independent geometry:
- writer primary positions equal the independently transcribed frozen primary oracle for every length;
- second-stage positions are non-empty, deterministic and disjoint from primary positions;
- a dual-collision poison position exists outside both sparse sets.

H2 — true-law retention:
- every exact ADD8/XOR row passes primary and second-stage checks;
- the unchanged complete exact proof accepts it.

H3 — stage-2 kill:
- every `stage2_collision` row passes the primary sampler;
- every such row fails the second-stage check;
- no complete proof is needed to reject it under the modeled candidate ladder;
- remaining relation-check bytes are strictly less than baseline `2N`.

H4 — dual-collision honesty:
- every `dual_collision` row passes both sparse stages;
- the unchanged complete exact proof rejects it;
- candidate remaining work is baseline `2N` plus exactly the second-stage observation cost;
- the experiment must preserve this regression instead of averaging it away.

H5 — information-yield accounting:
- report avoided exact-proof bytes for stage-2 kills;
- report added bytes for true and dual-collision rows;
- report the ratio `baseline_remaining_bytes / candidate_remaining_bytes` only for stage-2 kills;
- no CPU, wall-time, RSS or product-speed claim is permitted from modeled traffic alone.

## Decisions

- Any H1/H2 failure: `RETIRE_OR_REPAIR_SECOND_STAGE_FALSIFIER`.
- H1/H2 pass but any H3/H4 accounting or safety condition fails: `HOLD_SECOND_STAGE_FALSIFIER`.
- All H1–H5 pass: `ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY`.

`ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY` authorizes only a writer-integration experiment. It does not authorize enabling a second stage in the product writer. Integration must separately measure actual CPU/wall/RSS/cache behavior and prove that the extra sparse reads are worthwhile on generator-distinct positives, ordinary negatives and hostile dual-collision controls.

## Forbidden reinterpretations

Do not:
- remove or weaken exact proof;
- allow the second stage to accept a Law;
- tune sample count/locations after seeing results;
- use Genesis workloads;
- claim compression-ratio improvement (the representation is unchanged);
- claim runtime improvement from modeled bytes alone;
- average away the dual-collision overhead;
- add a reader-visible opcode, fallback codec or benchmark identity predicate.

## Genesis flags

Every result artifact must state:
- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`

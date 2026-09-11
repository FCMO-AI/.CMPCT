# ONE-G0.2 second-stage relation falsifier writer A/B preregistration — 2026-09-10

## Mission lock

Measure whether the hosted-green rejection-only second-stage oracle retains positive marginal information yield when integrated into the existing ONE-G0.2 general writer. The experiment may reduce exact relation-proof work; it must not change reader-visible representation, exactness, deterministic bytes, economic admission, predictor topology, or Genesis state.

This is a pre-Genesis transfer experiment. No Genesis workload may be executed.

## Baseline and candidate

Baseline:

`primary 16-point sampler -> economic admission -> exact ADD8/XOR proof -> Law/Surprise`

Candidate:

`primary 16-point sampler -> economic admission -> disjoint 15-midpoint rejection stage -> exact ADD8/XOR proof for survivors -> Law/Surprise`

The second stage is **rejection-only**. It cannot accept a Law. Full exact proof remains the only positive semantic authority.

The candidate must be exposed behind an experimental writer option whose default is disabled. No canonical format/version change is permitted.

## Frozen second-stage geometry

For each same-length prior/current file relation, derive the existing primary positions with the writer's current `_sample_positions`. Between every adjacent primary position `(a,b)`, inspect `a + (b-a)//2` only when strictly interior and not already primary. The result must match the previously hosted oracle geometry: 15 disjoint positions for the frozen measured lengths.

No adaptive sample-count tuning is permitted after results.

## Transfer corpus

Use deterministic generator-distinct trees that are not Genesis inputs. Each row contains a previous regular file and a current regular file and preserves normal authenticated archive construction.

Lengths: `256, 4096, 16384, 65536` bytes.

Families for both ADD8(+37) and XOR(0xA5):

1. `true`: exact relation;
2. `stage1_collision`: one poison byte at a second-stage position, so primary passes and candidate rejects before exact proof;
3. `dual_collision`: one poison byte outside both sparse sets, so both sparse stages pass and exact proof rejects;
4. `ordinary_negative`: deterministic unrelated target;
5. `sparse_damage`: deterministic relation with multiple damage bytes placed away from the first primary probe, representing a non-crafted near-relation.

Also include one mixed filesystem tree with files from all families plus empty file, directory, executable mode and symlink to ensure complete archive semantics stay invariant.

## Measurements

For each row build baseline and candidate repeatedly in alternating order on one hosted runner. Preserve medians for:

- process CPU seconds;
- wall seconds;
- complete wire bytes;
- discovery sample bytes;
- discovery exact-proof bytes;
- source-read bytes;
- peak RSS if available without changing the measured path materially.

The benchmark must independently open/reconstruct both wires and verify byte/file-system semantics. Candidate and baseline wires must be byte-identical for every row because the second stage only rejects candidates that baseline exact proof would also reject.

## Falsifiable hypotheses

H1 semantic/wire invariance:
- all baseline/candidate reconstructions equal source tree exactly;
- baseline wire == candidate wire byte-for-byte on every row;
- no reader-visible opcode/format/version change;
- determinism holds.

H2 proof-work causality:
- true rows: candidate exact-proof bytes equal baseline exact-proof bytes;
- stage1-collision rows: candidate exact-proof bytes are strictly lower than baseline, ideally eliminating the relation proof rejected by stage 2;
- dual-collision rows: candidate exact-proof bytes equal baseline exact-proof bytes and candidate records additional sample traffic;
- ordinary negatives must not gain new exact-proof work;
- preserve all rows individually; no aggregate averaging may hide a regression class.

H3 real compute economics:
- stage1-collision median candidate wall and CPU must not exceed baseline by more than the repository timing noise envelope and should improve materially at 4 KiB+;
- true and dual-collision medians must stay within baseline +5% relative or +0.003 s absolute per row, whichever is more permissive;
- ordinary-negative and sparse-damage rows must stay within the same timing envelope;
- aggregate median CPU and wall across all rows must be <=1.02x baseline.

H4 resource discipline:
- no target-sized persistent state added;
- no second source scan;
- peak RSS must not materially regress when measurable;
- candidate sample traffic must exactly account for the second-stage observations actually performed.

## Decision

Any H1 failure: `RETIRE_SECOND_STAGE_WRITER_INTEGRATION`.

H1 passes but H2/H4 fails: `HOLD_SECOND_STAGE_WRITER_INTEGRATION`.

H1/H2/H4 pass but H3 fails: `HOLD_SECOND_STAGE_WRITER_INTEGRATION_RUNTIME` and preserve the modeled-traffic win as insufficient.

All pass: `ADVANCE_SECOND_STAGE_WRITER_INTEGRATION`.

An ADVANCE result promotes only the rejection-only discovery optimization. It grants no Genesis score, no new compression-ratio claim, and no authority over unrelated Law discovery.

## Hostile interpretation rules

- A dual-collision regression is expected and must remain visible.
- If fixed sparse loads cost more CPU than the exact proof they avoid on realistic lengths, retire this implementation shape rather than tune lengths post hoc.
- If a later fused observation pass can expose an equivalent independent signal at lower marginal traffic, treat that as a causally new candidate and benchmark it separately.
- Do not weaken exact proof or allow sparse evidence to accept a Law.

## Genesis separation

Every artifact must state:
- `genesis_inputs_executed = false`
- `genesis_comparison_executed = false`
- `genesis_scoring_executed = false`
- `genesis_winner_selected = false`

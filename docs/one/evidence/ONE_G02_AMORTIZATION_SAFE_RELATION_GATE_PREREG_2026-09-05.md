# ONE-G0.2 — amortization-safe known-pair relation gate preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent evidence: `ONE_G02_SPARSE_RELATION_GATE_REPLAY_RESULT_2026-09-05.md`.

## Mission Lock / Referee

The unchanged sparse exact-shift gate retained every productive relation and classified every frozen case exactly, with a seven-size median gated/baseline of 0.81655x. Its all-sizes contract nevertheless failed because the gate has a fixed information cost of 160 compared bytes per pair: 4 KiB exceeded both the 1% read budget and the 1.03x runtime ceiling; 8 KiB exceeded the read budget.

This Builder does **not** change the sparse gate, its probes, support threshold, shift set, exact proof, or corpus. It changes only admission ownership: do not pay a turnstile whose own fixed information cost cannot satisfy the frozen work budget.

## Exact amortization boundary

For one relation pair the unchanged gate compares at most 160 bytes on the frozen path. The repository gate requires gate-compared bytes <=1% of relation bytes. Therefore a sparse gate cannot satisfy that budget when:

`160 / relation_bytes > 0.01`.

The exact boundary is:

`relation_bytes >= 16,000 bytes`.

This threshold is derived algebraically from the already-frozen detector and work budget, not selected from observed timing. It is not rounded to a benchmark size in code.

## Candidate dispatcher

For an already-known candidate relation pair:

- if `relation_len < 16000`, call the existing exact safe relation dispatcher directly;
- otherwise, call the unchanged sparse gate; only gate fires execute the exact safe relation dispatcher.

Thus small relations preserve baseline work/semantics, while sufficiently large relations may earn cheap falsification. The reader remains unchanged and performs no discovery.

## Frozen corpus and measurement

Reuse exactly the parent seven sizes and five-case mixed batches:

4, 8, 16, 32, 64, 128, 256 KiB.

Measure candidate versus the same ungated exact-safe baseline with A-B-B-A timing inside the native kernel and 41 outer medians / 16 batch calls, matching the parent experiment.

Report separately:

- candidate/baseline elapsed;
- gate compared bytes and read fraction (zero below 16,000 B because the gate is not invoked);
- gate fires/rejects only where the gate is eligible;
- productive relation retention and exact best shift;
- whether the row used direct proof or sparse-gated proof.

## Falsifiable hypothesis

The analytically bounded dispatcher will preserve exact relation decisions at every size, remove the parent gate's small-root read-budget failures, avoid >3% runtime regression on every row, and retain a seven-size median candidate/baseline <=0.95x.

## Frozen promotion gate

Advance the **known-pair turnstile architecture** only if all are true:

- identical enabled/disabled classification to baseline at every size/case;
- identical best shift for every productive relation;
- 100% productive retention;
- candidate gate-read fraction <=1% on every row (including zero on direct-proof rows);
- candidate/baseline <=1.03x at every size;
- seven-size median candidate/baseline <=0.95x;
- for every eligible size (>=16,000 B), at least one pair is cheaply rejected;
- pre-existing ONE semantic/hostile tests pass first.

## Claim boundary / disproof

Pair identity remains supplied by the frozen adjacent-pair batch. A pass establishes a viable **known-pair** execution architecture, not arbitrary-pair discovery.

If the candidate fails timing on the small direct-proof rows, wrapper/dispatch overhead must be measured; do not move the 16,000 B boundary based on timing. If it fails exactness, invalidate it. If large eligible rows lose their cheap rejection or semantics, retire the architecture.

If it passes, the next decisive integration is temporal/version adjacency in the ONE writer: pair identity is inherently known there, so the turnstile can be charged end-to-end without a rich content-certificate scan. Rich certificates remain cold discovery for contexts lacking a cheap pair relation.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows from this stage.
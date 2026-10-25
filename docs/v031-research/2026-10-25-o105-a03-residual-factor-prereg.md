# O105 — Prospective A03 Residual-Factor Oracle (2026-10-25)

**Status:** PREDICTION FROZEN BEFORE IMPLEMENTATION / MEASUREMENT. Research only; not product/release authority.

## Authority and non-overlap
Canonical `FCMO-AI/.CMPCT` `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, released v0.30.0/r24 unchanged. A03 in `docs/ASSUMPTION_LEDGER.md` asks whether residuals contain a second layer of reusable structure. Existing #452 trains decoder-visible dictionaries on PACK *source members*, #453 attributes VZIP memory, and #455/#456 own output-directory publication. This test is distinct: same-length **exact XOR residuals after one shared base**, and prospective *residual-space* factoring; no changing any owner implementation, test, threshold, format or CI comparator.

## Falsifiable primary question
Can a shallow (depth <=2) factor in **residual space** materially improve the **fully charged** storage/locality Pareto frontier over simpler complete-byte controls, beyond a friendly fixture?

Test fixed representation classes, no tuning by outcome:
A. independent Zstd of each original target;
B. solid Zstd of all original targets (strongest simple storage control, costly selective read);
C. one Zstd base + independently compressed XOR residual for each target;
D. same base + one Zstd concatenation of 8 residuals per group;
E. same base + one Zstd *position-major transpose* across each group of 8 XOR residuals (reversible; group decode);
F. one base + one actual residual root per 8-member group + independent Zstd of each XOR-of-residual delta (bounded two-level proof path).

Fully charge 64-byte archive root, 32 bytes per physical compressed owner, 24 bytes per logical target, 32-byte SHA per owner **within** owner charge, fixed 4-byte per file-length when variable, one copy of base bytes, all residual-root bytes, all encoded transform selectors and group membership. Do not gift a trained dictionary, source identity, or mutation locations to the decoder. For the fixed-size oracle, group membership by contiguous input order is encoded by target ordinals and 24-byte member charge; do not claim cost-free admission of better groups. Decode selected logical work = **all compressed physical owners required** and total reconstructed bytes including base and group/ancestor. Report both selected logical bytes and physical bytes plus dependency depth.

Primary optimistic H1 (can be falsified): E or F yields >=10% smaller *fully charged bytes* than the best of A/B/C/D on the positive correlated-edit regime **and** <=8x selected decoded-work amplification versus independent C. Require exact complete target equality, no false positive membership, no changed source. If H1 fails, retire/narrow this residual-factor mechanism for that regime, not rescue via other group sizes.

Generality H2: same mechanism also wins >=5% vs best simpler control on the independently generated **held-out differently structured** correlated family, while hostile independent mutations incur no claim of global gain; if H2 fails, preserve it as conditional seed at most. If only favorable fixture wins and the simpler solid control wins stored bytes, report no product headroom. Stronger negative kills the more general claim.

## Regimes and genuine controls
- Positive: random incompressible base, 32 versions, 4096 bytes each, common sparse edit patches plus smaller independent sparse edits.
- Held-out structural: deterministic structured/text-like base, changed lengths/positions or independent field-level grouping, 32 versions; separate seed and structural distribution.
- Hostile: random base, independent uncorrelated sparse edits per version, 32 versions.
- Flat negative: unrelated random 4096-byte targets, shared base is wrong explanation.
Each complete target input is fixed and identical across all compared arms. Use independently verified SHA256 of original and every reconstructed member. Stable deterministic public seeds; no fixture matching in production policy.
Record each arm's full charged bytes, compression wall+CPU, cold decompression wall, selected physical/logical work, dependency depth, Zstd version, repeats/ordering and raw records. At least five paired rotated runs after calibration; do not infer microsecond timing superiority from noise.

## Cheapest-rung falsifiers before spending full product compute
1. Derive mandatory metadata/base/root byte floor and bound achievable size gain before repeating compression.
2. Run direct whole-byte oracle and exact reconstruction; if H1 fails, no CMPCT format prototype and no exact-product benchmark credit.
3. Apply held-out perturbation only after a positive. Any result remains research/O0 only; a r24 materialized product must prove admission, byte exactness, independent integrity, selective read, recovery, CPU, RSS, temp I/O and native portability separately.

## Counterfactual and promotion limits
A stored-byte win that depends on one predetermined group ordering, hidden edited positions, uncharged root/metadata bytes, non-equivalent integrity, or a special fixture is NOT an A03 generic win. Comparator truth, existing frozen workflows, format r24 and release policy are immutable. This campaign neither releases nor merges code. Stop or change frame on a negative; no threshold gardening. Next activation should be able to reproduce the deterministic oracle, inspect raw individual measurements and reject the hypothesis.

## Concurrency
No overlap with open #452, #453, #455, #456, #457. One isolated research branch only; independently inspect current PRs again before any product code. Do not mutate `docs/discovery/STATE.json` while #440 owns reconciliation.

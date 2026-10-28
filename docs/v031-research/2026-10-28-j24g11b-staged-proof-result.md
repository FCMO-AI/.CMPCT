# J24G11b result — bounded-hot staging repairs repeated packed merge amplification

Date: 2026-10-28 UTC
Status: **DRAFT RESEARCH PRODUCT CANDIDATE, NO MERGE/RELEASE.** Observed installed-source Linux court is decisive on the exact short-orphan family; general product resource bounds and promotion parity remain unproven.

## Frozen causal chain and source custody

1. Published `main` v0.30.0/r24 remained untouched.
2. Original J24G10 #664 SQLite Reader: blob `0a8a7afa036cb4988b80836bcbe550c3b5d0bb40`.
3. Protected original packed J24G11 #667: branch HEAD at prereg parent `19f8d0313a93655af05a365d1777a7a303a550be`; Reader blob `4bcedb059316171963d258fc93caaa49fec56f12`; original long-chain hosted court [#40672948612](https://github.com/FCMO-AI/.CMPCT/actions/runs/40672948612) **SUCCESS** (2.141×/2.181× faster than SQLite for 16,400 one-chain malformed signed footers, no full promotion credit).
4. Independent J24G11b prereg `c363ec7dcec370509a8318dae8d5603fe5835808` precedes source edit `d7cf434457ca621a1e605aab33534a1f8f5e95b9`.
5. New staged Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. Source code/existing decoder algorithms unchanged apart from bounded proof-store management.
6. Exact installed hosted **first source/evaluator** HEAD `55bad143f543dbf7683cae4b3b7b37bbc5dfee1f` [GitHub Actions #40673704612](https://github.com/FCMO-AI/.CMPCT/actions/runs/40673704612) **SUCCESS**, original raw artifact retained. Subsequent evidence-only edits do not modify Reader blob; independently audited final-head evidence must be checked separately.

## Why this is a decision-changing negative and repair

On the earlier #667 packed implementation, a long malformed 16,400-ancestor chain was stored in one initial sorted-array build and was a 2.14× win versus SQLite. However, many independent two-footer malformed chains call `update` repeatedly with two keys, causing a full O(N) array rebuild each time. A detached Python 3.13 instrument, not product evidence, counted 32,892,944 repeated element visits to grow 16,384→20,000 offsets in two-key updates (approximately 5.006s array vs 28.964ms SQLite).

The new implementation amortizes the packed tier by preserving an exact bounded hot staging set (max 16,384) and merging in one batch. The upper stored-payload limit remains 1 MiB; overflow transfers *both* packed and staged proof positions to the original SQLite fallback. SQL is physically committed; no approximate skip, new archive bytes, codec, dependency or weakened evaluator.

## First-host actual Reader measurements

GitHub Actions #40673704612; Ubuntu 24.04, Python 3.11, actual installed candidate, identical 1,458,968-byte r24 archive from first-party Builder plus **9,000 pairs of SHA-authenticated orphan footers**, actual source-bound #667, #664 and unbounded-set control, three alternated matched repetitions, full read/range/verify/checkpoint for every arm.

| Reader | Same-archive open/read/verify median wall | Actual decoder calls |
|---|---:|---:|
| J24G11 #667 previous packed | **884.667045 ms** | 18,001 |
| J24G10 #664 SQLite | **141.205279 ms** | 18,001 |
| J24G11b staged packed | **102.291108 ms** | 18,001 |
| Unbounded Python set research control | **100.653267 ms** | 18,001 |

**Measured decisions:** staged is **8.64852× faster than J24G11**, **1.38043× faster than SQLite** and only **1.63% slower than unbounded Python-set oracle** for this fixed synthetic hostile family. Identical decoded work confirms savings belong to *proof-store representation/lifetime*, not weakened metadata decoding. The source-bound archive SHA-256 is `32dee09fbee10015044a87078e7bc5998931b89924fa6999c730a87ae6750a8a`.

First-party Writer legitimate `append_rename` control: staged **0.093840ms**, old packed **0.094979ms**, SQLite **0.095054ms**, 11 repetitions, 2 decoder calls each; no adverse signal. These are submillisecond noisy numbers, not a general speed gain.

## Proof correctness and accounting

The hosted in-process *untimed* proof oracle submitted 1,000 two-key incremental updates in **2.460046 ms** for 2,000 staged keys, separately crossed the 16,384 hot threshold to merge packed exactly, then transferred hot and packed to physical committed SQLite above the 1MiB payload ceiling. A second SQLite connection verified **131,075 exact keys** and the temporary DB was deleted. This verifies proof-store membership for the checked cases, not the full Reader's RSS.

## Strongest negatives and remaining debt

- Long-invalid-chain 2.14–2.18× #667 win is preserved as **historical** source evidence; J24G11b's own long-chain cost was not remeasured in this first hosted court.
- A Python `set` still slightly wins absolute time on short-orphan hostile recovery, but is unbounded memory. Packed+staging is a different memory/time Pareto tradeoff.
- No global bound on per-chain `seen` and decoded `chain`, total process RSS, temporary SQLite bytes, physical I/O, or elapsed CPU for arbitrarily large data. Fixed 1MiB is only the packed payload tier, not total heap.
- Concurrent same-inode footer mutation [#654](https://github.com/FCMO-AI/.CMPCT/pull/654), Windows/macOS correctness and full release parity remain unresolved.
- Historical J24G11/J24G10 source-locked workflows correctly FAIL if asked to certify the new Reader blob; do not change their historical source contract to force green.
- General Tests on this draft cannot be called green until exact-head terminal results and any inherited release-fingerprint/surface red are distinguished from new semantic failures.

## Counterfactual and decision

A cheap prospective **many-independent-short-ancestries** perturbation would have revealed the packed-array O(N²) ownership leak before promoting the one-long-chain speed claim. The practical lesson is to include both a large single batch and many tiny batches when evaluating mutable exact proof stores. This lesson currently supports only this family; do not edit the global Discovery Engine policy from one case.

**Decision:** preserve J24G11b as a stronger bounded-tier research candidate, not release. First next executable test: full same-host identical signed physical corpus comparing staged vs #667 vs #664 on one-long-chain, alternating irregular, random irregular, and independent short chains with repeated CPU/RSS/temp-I/O measurements; then cross-host and concurrent-source policy. Remove the packed family entirely if it loses to simpler exact bounded alternatives on the full Pareto surface.

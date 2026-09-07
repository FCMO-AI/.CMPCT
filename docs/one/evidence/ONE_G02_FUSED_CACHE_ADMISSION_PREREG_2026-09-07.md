# ONE-G0.2 fused-cache admission rehabilitation — preregistration

Date: 2026-09-07
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission Lock / Referee

Exact-head whole-writer evidence at `66829c1af37d164352046dcf29db2ffabc790ca3` established a split result. Positional fused-cache updates survived system-level Amdahl dilution strongly, but workloads with no positional cache reuse regressed by about 32% because the cache path paid per-block SHA-256 plus full fused recomputation. The terminal result was `OPEN_CACHE_ADMISSION_DEBT`.

The cache is therefore not an unconditional observer replacement. The rehabilitation target is a bounded writer-side pre-admission probe that rejects clearly reuse-poor updates before the expensive fused-cache path runs, while preserving the large positional-update gains.

## Baselines

Scientific baseline: fresh `observe()` inside the same root-hash-charged research-writer envelope used by `one_g02_full_ingest_fused_cache.py`.

Mechanism control: unconditional `observe_incremental()` using the same previous fused cache.

Candidate: bounded stratified content-identity probe -> either unconditional fused-cache observer or fresh observer. No reader state or ONE bytes change.

## Mechanism

Probe at most 8 stratified prior block positions. At each sampled position hash the current block with SHA-256 and compare `(digest,length)` to the corresponding previous fused-cache block identity. Admit fused-cache observation only when at least 25% of sampled positions match. Otherwise use ordinary fresh observation and do not construct a new fused cache during that rejected update.

The 25% rule is frozen before result. It is deliberately permissive: the purpose is to reject zero/near-zero positional reuse, not to estimate exact reuse percentage. Actual cached blocks remain independently SHA-validated and sealed before reuse; the probe is performance policy only and can never authorize reconstruction.

## Invariants

- candidate observation exactly equals independent fresh `observe()` opportunity semantics;
- same canonical writer wire/stats as fresh baseline on every row;
- same relation classification and independent segment-plan oracle when admitted downstream;
- exact VM reconstruction of previous/current roots;
- root SHA-256, Program validation and direct canonical emission remain inside the timed writer envelope;
- no reader-visible cache, opcode, format or canonical-version change;
- malformed/incompatible prior cache must fail admission safely to fresh observation;
- probe bytes/hashes are charged to the candidate timing and traffic ledger;
- no threshold may move after results.

## Frozen matrix and gates

Reuse the same 64 KiB / 256 KiB matrix and 15 paired alternating repetitions from the whole-ingest falsifier:

- `exact_repeat`: cache must be admitted; total wall and CPU <=0.95x fresh baseline;
- `one_block_edit`: cache must be admitted; wall and CPU <=0.98x;
- `eight_block_edit`: cache must be admitted; wall and CPU <=1.02x;
- `shift_plus1`: cache must be rejected; wall and CPU <=1.05x;
- `independent_random`: cache must be rejected; wall and CPU <=1.05x.

Every expected admission/rejection is itself a frozen gate. A candidate that wins timing by accidentally bypassing intended productive cache rows or by admitting the hostile rows fails.

## Cost model

Record total wall/CPU and stage medians, probe sampled/matched blocks, probe source/hash bytes, admitted flag, cache reuse/recompute bytes when admitted, retained cache payload when present, canonical wire bytes, reader work/materialization, downstream relation/segment work and exact reconstruction.

A fallback row explicitly returns no new fused cache. That breaks cache continuity after a rejected update and is regression debt, not free behavior. The experiment tests whether avoiding ~32% immediate carrying cost is worth preserving as an admission mechanism; later work must decide how/when a fresh cache can be rebuilt without reintroducing the rejected cost.

## Disproof / terminal decisions

- any semantic/oracle/wire divergence -> `INVALIDATE_CACHE_ADMISSION`;
- any expected admission classification mismatch -> `REJECT_CACHE_ADMISSION_CLASSIFIER`;
- any positional performance gate failure -> `REJECT_CACHE_ADMISSION_PRODUCTIVE_DEBT`;
- any hostile >1.05 wall or CPU -> `HOLD_CACHE_ADMISSION_CARRYING_COST`;
- all gates pass -> `ADVANCE_CACHE_ADMISSION_REHABILITATION`.

## Hostile Reviewer

Strongest expected objection: the probe hashes bytes that an admitted cache path hashes again. This deliberately duplicates up to 32 KiB of SHA input. The hypothesis survives only if that cheap bounded duplication is dominated by the fused observation work it avoids on reuse-rich updates, while remaining small enough on rejected updates to erase most of the observed ~32% regression.

A second objection is continuity: rejecting a cache also declines to build the next cache. That is acceptable for this falsifier but prevents promotion as a complete incremental compiler policy until cache re-seeding economics are measured.

## Claim boundary

A pass establishes only a useful writer-side admission policy for the existing positional fused-observation cache in the frozen adjacent-version research envelope. It does not establish arbitrary-shift cache reuse, persistent cache re-seeding policy, authenticated physical ingest, product-native speed, RSS authority, density gains or v0.29/v0.30 supremacy.

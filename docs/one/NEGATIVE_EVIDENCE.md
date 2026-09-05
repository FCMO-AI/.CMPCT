# CMPCT ONE — Scoped Negative Evidence

**Experimental line:** `ONE-G0.2`  
**Primary branch:** `research/cmpct1`  
**Purpose:** preserve falsified discovery assumptions and explicit reopening predicates so later activations do not rediscover or silently generalize them.

This ledger is research evidence, not format or release authority. Failures below concern encoder-side nomination economics only. Exact reuse is always byte-proven before a Law candidate may survive; no failed selector can make reconstruction incorrect.

## G0.2-N01 — Synthetic Gear identity was not inherited CMPCT Gear

**Tested regime.** The early `one_g02_gear_oracle.py` called a SplitMix-derived table “historical Gear”. The frozen v0.29 resemblance implementation instead derives `GEAR[i]` as domain-separated BLAKE2b with person `cmpct-gear-v1`.

**Decision.** The synthetic table is retired for inherited-Gear claims. Current G0.2 Gear experiments bind to the exact inherited derivation.

**Causal interpretation.** Similar mechanism shape is not signal identity. Results about one deterministic table do not establish results about another.

**Reopening predicate.** A different table may be tested as a new signal family only with its identity explicit; it may not inherit historical-CMPCT claims.

## G0.2-N02 — Sparse masked Gear alone is not a complete reuse selector

**Frozen experiment.** `benchmarks/one/one_g02_gear_replacement_ab.py`, schema `cmpct-one-g02-gear-replacement-ab-v3`.

**Exact-head evidence.** Source `92d11298cbc8fe6deed8210613cb31c75d8a7f2a`, workflow `33931050010`, artifact `9958592877` (`sha256:cad01f3056f62c61f74d64c746dd325801ddc9853023c4c291d0ccbf5632dfa2`).

**Result.** A `1/1024` masked Gear selector preserved the tested long aligned relationships and recovered the 524,288-byte one-byte-shifted version relation that the aligned fixed selector missed. It also reduced retained discovery payload strongly on random/large regimes. However, deterministic periodic 64 B, 128 B and 256 B bases had **zero qualifying Gear anchors** and lost 4,032 B, 3,968 B and 3,840 B of fixed-selector opportunity respectively.

**Decision.** `reject_sparse_gear_as_complete_replacement`.

**Causal interpretation.** Expected anchor density is not a worst-case spacing guarantee. A periodic Gear-state cycle can contain no masked state and remain invisible forever.

**Reopening predicate.** A selector derived from the same content signal must provide an explicit nomination-spacing guarantee while retaining insertion/shift stability and bounded state.

## G0.2-N03 — Bounded local retention plus sparse global Gear still has long-cycle starvation

**Frozen instruments.** `benchmarks/one/one_g02_tiered_gear_ab.py` and `benchmarks/one/one_g02_anchor_starvation.py`.

**Tested regime.** A deterministic 8 KiB basis from seed `4876` contains zero sparse masked Gear anchors. The 64-entry aligned local horizon represents only 4 KiB of recent 64-byte phases.

**Result.** `basis || basis` contains an exact 8,192-byte reusable second copy. The local+masked selector loses it after the first copy's matching phases have been evicted.

**Decision.** The 64-entry local + sparse-global policy is retired as a complete replacement, despite surviving the friendly short-period and ordinary shifted cases.

**Causal interpretation.** A finite local horizon repairs only periods within that horizon; it does not repair unbounded gaps in the global selector.

**Reopening predicate.** A global selector must bound nomination gaps independently of friendly anchor statistics.

## G0.2-N04 — Absolute-position gap fallback repairs starvation but loses shift invariance

**Frozen instruments.** `benchmarks/one/one_g02_bounded_gear_ab.py` and `benchmarks/one/one_g02_shifted_starvation.py`.

**Result.** For the zero-anchor 8 KiB basis, a forced global nomination after a 4 KiB absolute gap recovers the aligned `basis || basis` relation. The same content as `basis || b"X" || basis` receives different fallback phases after the one-byte insertion and recovers **zero** reuse bytes.

**Decision.** `reject_coordinate_gap_fallback_as_shift_robust_replacement`.

**Causal interpretation.** A coordinate-timed fallback can guarantee spacing or shift invariance, but not both: insertion changes the absolute phase even when the repeated content is unchanged.

**Reopening predicate.** Global selection must be content-derived and have a bounded nomination gap.

## G0.2-C01 — Rolling Gear minima survive current opportunity falsifiers, but compute blocks promotion

**Candidate.** `benchmarks/one/one_g02_minimizer_gear_ab.py`, schema `cmpct-one-g02-minimizer-gear-ab-v3`. The selector retains one Gear stream at two horizons: a bounded local aligned cache for short relationships and the rightmost minimum Gear state over a 4,096-position rolling window for global relationships. This is encoder discovery only; emitted candidates remain generic exact reuse Laws.

**Exact-head evidence.** Source `970326480938d4461bdd5f99bad152b51bda129e`, workflow `33933740375`, job `101217501634`, artifact `9959505729` (`sha256:c17fadcc63202a745ce115325cc6d354b68603af9592393fe6f1f8f570ba77ec`); `50 passed` in `tests/one`.

**Opportunity result.** No fixed-selector opportunity loss was observed across the frozen deterministic matrix. The minimizer also recovers:

- 524,288 B from the ordinary one-byte-shifted 512 KiB version pair where aligned fixed chunks recover 0 B;
- 8,192 B from the zero-sparse-anchor 8 KiB aligned adversary;
- 8,192 B from the same adversary with a one-byte insertion.

**State result.** On the hosted Python evidence run, modeled retained state was 9,632 B vs 262,144 B for fixed indexing on random 1 MiB (3.67%), 5,440 B vs 262,144 B on the shifted 512 KiB pair (2.08%), 5,504 B vs 131,072 B on an exact 512 KiB pair (4.20%), and 1,904 B vs 16,384 B on repeated 64 KiB bases (11.62%). On repeated 4 KiB bases, the current candidate is worse: 1,296 B vs 1,024 B (126.56%).

**Read result.** Negative random/compressed cases remain one source-read equivalent with no proof rereads. Exact repeated relationships pay essentially the same complete proof-read traffic as the fixed baseline. Shifted relations deliberately add about one extra input-sized exact proof because the fixed selector finds no corresponding opportunity.

**Compute result / blocker.** The Python reference is **not competitive**. More importantly, the exact-head native recurrence proves the blocker is not just interpreter overhead. On 1 MiB large cases the Gear-only recurrence is about 2.02–2.10 GiB/s while the current rolling-minimum kernel is only 90.35–92.12 MiB/s: **22.30x–23.14x** elapsed over Gear-only, with about **9.90–10.09 ns of incremental minimizer work per input byte**. Observed live queue state remains small (roughly 2.4 KiB in the microkernel), so state capacity itself is not the explanation.

**Current decision.** `opportunity_semantics_survive_current_falsifiers_compute_review_required`. Do **not** replace `experiments/one/observe.py` with this selector yet and do not claim product-speed or stored-byte superiority.

**Strongest self-critique.** The rolling-minimum selector has the right current invariants, but its monotonic-minimum maintenance is structurally expensive even when compiled. Low retained state is not enough; CMPCT1 is a density + speed + compute-efficiency project. The selector must earn its opportunity value per CPU and memory traffic before promotion.

**Next falsifier / reopening predicate.** Replace the same exact rightmost sliding-minimum semantics with a causally different bounded maintenance algorithm and compare exact emitted positions, compute, and state/memory traffic. The next experiment must not change Gear identity, minimizer span, nomination semantics, proof rules, or reader representation.

## G0.2-N05 — Ring-address arithmetic is not the primary remaining rolling-minimum cost owner

**Frozen instruments.** `benchmarks/one/one_g02_minimizer_wrap_ab.py` and `benchmarks/one/one_g02_minimizer_mask_ab.py`, with compiled kernels in `one_g02_minimizer_branch_kernel.c` and `one_g02_minimizer_mask_kernel.c`.

**Exact-head evidence.** Source `970326480938d4461bdd5f99bad152b51bda129e`, workflow `33933740375`, job `101217501634`, artifact `9959505729` (`sha256:c17fadcc63202a745ce115325cc6d354b68603af9592393fe6f1f8f570ba77ec`). All semantic tuples matched the independent Python recurrence.

**Frozen hypothesis and disproof.** After the earlier branch-wrap A/B showed that runtime modulo owned part of the cost but failed its 15%-on-every-large-case promotion rule, the masked-ring follow-up asked whether residual ring addressing still owned at least 10% on **every** large case, with no tested case more than 5% slower. The 4,096-position span was already frozen and is a power of two, so replacing wrap arithmetic with `& 4095` changed no selector semantics.

**Result.** The mask is useful but not decisive. Relative to branch-wrap it improved large-case medians by only 5.15%–8.74%: random 1 MiB `9.298 ms -> 8.575 ms` (8.43%), zlib-random `9.240 -> 8.788 ms` (5.15%), exact pair `9.300 -> 8.552 ms` (8.74%), shifted pair `9.327 -> 8.602 ms` (8.43%), repeated-64-KiB basis `8.903 -> 8.253 ms` (7.87%). On the 16,385-byte shifted-starvation adversary it regressed `67.091 us -> 71.538 us`, **+6.63%**, violating the frozen 5% no-regression limit. The single boundary case at 4,160 B improved strongly (33.1%), but it is not representative of sustained large-input cost.

**Decision.** `retire_ring_addressing_as_primary_remaining_owner`.

**Causal interpretation.** Removing modulo and then reducing the remaining wrap arithmetic can recover a useful single-digit percentage, but it cannot explain the roughly 22–23x gap between Gear-only and current compiled minimizer maintenance. The primary remaining owner is inside the monotonic-minimum maintenance itself: value comparisons, variable pop/expiry control flow, and associated queue memory traffic.

**Reopening predicate.** Ring addressing may be revisited only as part of a new maintenance layout/algorithm whose total measured effect meets a preregistered material threshold across both large and hostile-small cases. Do not resume isolated wrap micro-tuning.

## External conceptual corroboration, not repository authority

The selector question matches the classic document-fingerprinting distinction between threshold sampling and winnowing: fixed threshold sampling has no upper bound on gaps, while selecting a minimum in every rolling window provides a bounded local guarantee and preserves fingerprints inside sufficiently long unchanged substrings after shifts. Repository experiments above remain the authority for CMPCT1 decisions; literature is explanatory support only.

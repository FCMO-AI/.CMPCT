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

**Exact-head evidence.** Source `92d11298cbc8fe6deed8210613cb31c75d8a7f2a`, workflow `33931050010`, job `101209548157`, artifact `9958592877`; `50 passed` in `tests/one`.

**Opportunity result.** No fixed-selector opportunity loss was observed across the frozen deterministic matrix. The minimizer also recovers:

- 524,288 B from the ordinary one-byte-shifted 512 KiB version pair where aligned fixed chunks recover 0 B;
- 8,192 B from the zero-sparse-anchor 8 KiB aligned adversary;
- 8,192 B from the same adversary with a one-byte insertion.

**State result.** On the hosted Python evidence run, modeled retained state was 9,632 B vs 262,144 B for fixed indexing on random 1 MiB (3.67%), 5,440 B vs 262,144 B on the shifted 512 KiB pair (2.08%), 5,504 B vs 131,072 B on an exact 512 KiB pair (4.20%), and 1,904 B vs 16,384 B on repeated 64 KiB bases (11.62%). On repeated 4 KiB bases, the current candidate is worse: 1,296 B vs 1,024 B (126.56%).

**Read result.** Negative random/compressed cases remain one source-read equivalent with no proof rereads. Exact repeated relationships pay essentially the same complete proof-read traffic as the fixed baseline. Shifted relations deliberately add about one extra input-sized exact proof because the fixed selector finds no corresponding opportunity.

**Compute result / blocker.** The Python reference is **not competitive**. Relative to the current fixed observer it measured 4.38x elapsed on random 1 MiB, 4.34x on zlib-compressed random, 4.22x on an exact 512 KiB pair, 4.27x on the one-byte-shifted 512 KiB pair, and 4.09x on the shifted starvation adversary. Tiny periodic 4 KiB inputs are ~1.83x–1.96x slower even after global minimizer work is structurally disabled when the input is too short to mature a selector window.

**Current decision.** `opportunity_semantics_survive_current_falsifiers_compute_review_required`. Do **not** replace `experiments/one/observe.py` with this selector yet and do not claim product-speed or stored-byte superiority.

**Strongest self-critique.** The rolling-minimum algorithm has the right current invariants, but Python spends substantial per-byte interpreter/deque work to obtain them. Low retained state is not enough; CMPCT1 is a density + speed + compute-efficiency project. The selector must earn its opportunity value per CPU and memory traffic before promotion.

**Next falsifier / reopening predicate.** Measure the same Gear/minimum recurrence in a bulk/native observation microkernel, preserving the exact G0.2 vectors and complete queue/index/proof accounting. Promotion requires a credible memory-bandwidth-oriented path and must also hostile-test collision poisoning / bounded multiple-source handling rather than assuming one 64-bit signal source is always sufficient.

## External conceptual corroboration, not repository authority

The selector question matches the classic document-fingerprinting distinction between threshold sampling and winnowing: fixed threshold sampling has no upper bound on gaps, while selecting a minimum in every rolling window provides a bounded local guarantee and preserves fingerprints inside sufficiently long unchanged substrings after shifts. Repository experiments above remain the authority for CMPCT1 decisions; literature is explanatory support only.

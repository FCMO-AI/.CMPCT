# J24B03-M2 — high-cardinality direct RAW safety-guard macro falsifier (prospective)

**Date:** 2026-10-27 UTC. **Status:** PRE-RESULT; no measurement available at preregistration. **Owner:** existing draft PR #609, Phased3. **Parent scientific court:** J24B03-M [host run 40582356902](https://github.com/FCMO-AI/.CMPCT/actions/runs/40582356902).

## Scientific question and prospective prediction

J24B03-M measured 65,536 legal direct S_BLOB references to a single 128-byte RAW physical block. Candidate direct-size/BHDR guard adds +19.582 ms on the complete selective-read stage (+24.33%) and +22.709 ms on the full open–read–close session (+12.54%), narrowly below the preregistered absolute 25 ms veto. This is **not** a claim of no cost. The candidate guard executes each read and the inherited source has no memoized direct physical-header proof.

**Primary question:** Does the original J24B03-M **unchanged numerical veto** fire when held-out legitimate logical-reference counts are increased to 131,072 and 262,144? Prediction from prior measured per-call tax (not a result): at least one high-cardinality scale will exceed both +25 ms session wall/CPU and 1.10× relative session wall/CPU. **Kill prediction:** both scales stay below the original conjunction, after exact-source 3-round ABBA; retain quantitative costs either way. Stronger alternative explanation: longer index opening and preflight may dilute relative 1.10× even when absolute read tax grows; CPU scheduling variance may also change the ratio.

## Immutable control and evidence

- **Published baseline:** original `main@80c358f8824ec1b20d349c92ed94c898090969b0` in separately installed `frozen-baseline/src`, not a reconstruction of old algorithms.
- **Candidate code:** precisely the branch's existing `src/cmpct/reader.py` and `src/cmpct/validation.py`; their actual SHA-256 and import paths checked in every worker, no modifications to Reader/Builder, physical wire, on-disk format or inherited H/M frozen results.
- **Input:** Builder-independent genuine revision-24 archive generated using the original M instrument's authenticated frame/index construction: one RAW 128-byte physical owner with 1, 131,072 or 262,144 distinct valid direct-file rows. No malformed input, exactly same archive per A/B arm, full physical bytes charged, complete content and selective-byte checksum verified. The 1-file profile is a control and cannot trigger the macro verdict.
- **Measurement:** 3 fully independent ABBA rounds at each scale (36 processes), order released/candidate/candidate/released. Each worker measures cold-open, selective reads of all logical rows, complete session CPU/wall, separate strict-preflight CPU/wall, peak process VmHWM. Process startup excluded; copies/index parsing/extractor metadata included. All original observations retained as JSON, plus SHA-256 of source, binary archive, input identity, and measured output checksum. A stdlib-only referee independently recomputes medians/verdict, checks source/image/paired identity and rejects mutated receipts.
- **UNCHANGED J24B03-M veto:** if at either 131,072 or 262,144 files, candidate/full-session **both** median wall AND median CPU ratios >=1.10 **and** their two absolute additions >=25,000,000 ns, OR candidate VmHWM >=8,192 KiB higher, mark `MATERIAL_DIRECT_SESSION_DEBT`. Preflight separately requires wall & CPU >=1.15× and both +50,000,000 ns to mark `MATERIAL_DIRECT_PREFLIGHT_DEBT`. Combine decisions exactly as M; do not retroactively change thresholds or overwrite M's historical non-veto. Preserve all absolute/relative negatives.
- **Guardrails:** the experiment probes only deduplicated direct RAW read range at one host/CPU/Python configuration. It is not an official release comparison, a proposed format change or evidence of arbitrary-file overhead. Never drop safety checks to improve the benchmark.

## Alternatives / PARETOBONK / decision transfer

1. Repeating M at 65,536 has weaker information value than testing whether its near-veto extends linearly.
2. Tuning the numerical 25-ms criterion after seeing results is forbidden; retain it exactly.
3. Moving the guard to eager archive-open validation can reduce per-call work only by paying a distinct bounded startup/memory cost, and needs independent semantics and source-mutation review; not presumed acceptable.
4. A genuine material upper-scale veto should hold #609 for bounded architectural rehabilitation before a product merge; a second non-veto narrows the claim and returns priority to #569's larger measured 27–28× chunk-open debt.
5. No policy/STATE.json mutation; #574 owns its staleable state reconciliation. No new PR needed unless conflict arises.

**Before-results declaration:** branch head at preregistration was `ff815fb77708c396b1554cd7a61f3debbedb1ede`. Any succeeding implementation must preserve J24B03-M sources/evaluator, negative J24B03-H, and this prospective threshold.

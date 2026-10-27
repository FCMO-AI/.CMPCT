# O218 — native CPython PyList admission oracle: confirmed micro headroom, no product credit

2026-10-27 UTC. **Science tier:** detached source-guided microbenchmark. **Disposition:** `MICRO_NATIVE_HEADROOM`; product integration/portability `UNMEASURED`. This closes the preregistered cheap rung, **not** the J24C02 v0.31 Reader release gate.

## Source and preregistration
- Parent O216 research PR #570 exact `6989b25640be2c82436bb77ec545dd15816f698b`. Independent question preregistered at `94a7eaf09ba18131a4eab7111e3f0ce6a70e8047`, before C implementation/observations.
- Strict original validator Git blob `51c2849061f99a4afeddb7666956b24566ce7de0`, unchanged; shipping v0.30.0/r24 and J24C02 #569 remain unchanged.
- O217 Counter-style native-backed multiplicity #575 returned only 1.080x/1.069x repeat improvements vs O216 and 0.789x distinct regression. The present alternative changes the **execution boundary** via direct `PyList_GET_ITEM` scanning, not grouping or a different representation.

## Exact hosted evidence
- Scientific run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40464142815 , result **SUCCESS**, code/test HEAD `bb9dd50880fd9a1661c26809ab6bf0ee00c1fd1f`.
- GitHub original raw artifact CPython 3.11 **#12715294460**, 3.13 **#12715601413**. Both contain `raw.json`, independent SHA identifiers for HEAD/Reader/validator and logs.
- Each host executed **312 repeated A/B/C samples** across 8 structural profiles, with 16 hostile controls and 5,000 deterministic hostile fuzz comparisons; all expected positive cases pass and native accepts no unsupported case. No oracle/unsafe timing arm was used for product credit.
- Independent audit against the **original ZIP artifacts**, recomputing every profile median/speedup and checking file CRC, code hashes, 624 raw observations, identical MessagePack fixture fingerprints across hosts and false-accept records: **PASS** (audit kept as session artifact; hashes below).

### Same-host medians (milliseconds)

| Source / profile | CPython 3.11: Python→native | Native factor | CPython 3.13: Python→native | Native factor |
|---|---:|---:|---:|---:|
| 65,536 repeated | 4.420755 → 0.616012 | 7.1764x | 5.179415 → 0.799042 | 6.4820x |
| 65,536 all-distinct | 4.361895 → 0.603528 | 7.2273x | 5.335037 → 0.824129 | 6.4735x |
| 262,144 repeated | 18.136579 → 2.475198 | 7.3273x | 20.927853 → 3.189034 | 6.5624x |
| 262,144 all-distinct | 17.593649 → 2.756173 | 6.3834x | 21.456617 → 3.563097 | 6.0219x |

The preregistered **3x at 65,536 and 262,144, both repeated and distinct** is met on both Python versions. Mixed 4,096-owner runs were slower (4.8842–4.9091x at 262,144), still above 3x. They prohibit extrapolating a constant 7x advantage.

## Mechanism and strongest control
- Candidate C code consumes already-decoded Python list references and physical blob rows, checks every reference's exact built-in integer type, bounds, every row's 5-item shape and length, accumulates length with overflow guard. It performs **no sampling, grouping, new format or precomputed/stored index**.
- Ordinary Python control uses exact guarded integer and list read accumulation; a second stricter Python model pays per-row structural checks. Native False means run the original unchanged full strict validator, preserving its diagnostic/failure contract. It does **not** mean a valid file should be rejected, and the native helper cannot replace upstream index structural validation.
- Eight deterministic MessagePack source families were packed/unpacked and fingerprints verified identical between 3.11 and 3.13, preventing fixture identity drift from explaining the result.
- This result distinguishes CPython interpreter dispatch overhead from linear scanning itself. It does not eliminate O(number of references) work.

## Failure modes, limitations and full-system debt
1. **Not an installed CMPCT Reader A/B**: the Python control is source-guided; the original full Reader O216 cold-open measurements ~6.36/25.13 ms are inherited external evidence and are **not directly comparable** or subtractable from detached micro timings.
2. **Native maintenance/exported cost**: CPython-specific C ABI, compilation, three-platform binary wheels, other interpreters, optional-helper fallback, code-review/security surface and operational support are uncharged. Windows/macOS, ABI compatibility and actual peak RSS are unmeasured.
3. **Strict semantics**: unusual `int` subclasses, huge integers beyond `Py_ssize_t`, malformed row objects and overflow fall back rather than being silently accepted. Full authenticated index and multiple-generation/transaction/range/extraction contracts were not rerun.
4. **No product perf / release evidence**: no official full ZIP-parity, corpus, create/extract/read/portability or post-install tests. No C module entered the CMPCT product. No change to format, native ABI, benchmark, threshold, validator or Reader.

## Scientific decision and next cheapest discriminant
**Decisive lower-rung headroom established.** The Counter hypothesis is not rehabilitated; a *different execution architecture* deserves a one-shot owner-coordinated full Reader composition/cost test if its portability carrying cost is acceptable. Test the exact parent and optional-native candidate on authentic revision-24 65,536/262,144-ref files with same-index strict rejection, historical O212/O214/O215/J24C02 courts, full cold-open CPU/wall/RSS, independent processes, real compiled-wheel availability on Ubuntu/macOS/Windows and measured fallback. Compare strongest existing O216 under identical semantics. Kill/reject productization if end-to-end benefit or portability economics fail. Do not mutate owner #569 or issue parallel product implementation by default.

Discovery Engine: one primary question, no ownership collision identified; Counter was explicitly a negative predecessor. Prospective policy lesson not earned from a single native positive; do not mutate normative Discovery Engine or `STATE.json`. In hindsight, native direct PyList dispatch was a cheaper root-mechanism probe than another Python histogram candidate, but this has not been shown prospectively to improve search throughput repeatedly.

**Release:** no merge, no version, no change of format, no full product success claim.

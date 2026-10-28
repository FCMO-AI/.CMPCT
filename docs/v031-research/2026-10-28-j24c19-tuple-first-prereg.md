# J24C19 — Tuple-first MessagePack owner admission: preregistration

Date: 2026-10-28. **RESEARCH ONLY.** This file is frozen before any new experiment code or observed results.

## Exact parent and reason to change frame

Parent is #676 at `3b6a73f9205f40f11124cd9ff332407e52cebb93`, not main; the released v0.30.0/r24 product remains untouched. J24C16 proved that public mutable chunk references invalidate cached range proofs; #676 sealed the references by converting the original mutable list to tuple **after** native admission, and two honest #662 comparisons measured +13–24% session cost. J24C18 #679 falsified per-entry C tuple assembly against the simpler CPython tuple copy. Three adjacent attempts force a representation/ownership frame change, not another C-loop tweak.

**No collision:** J24G16 #681 owns predecode token-count/resource admission. This experiment owns only the *post-decode in-memory mutability/ownership construction cost*; no changes to #681, production Reader, parser safety or shared Discovery state.

## Primary falsifiable question

For an unchanged, SHA-bound revision-24 MessagePack index payload with one genuine `S_CHUNKS` member of N refs, can `msgpack.unpackb(..., use_list=False)` followed by **schema-specific structural thaw** construct immutable chunk refs with materially less in-process CPU and wall time, without a second O(N) tuple-copy, than current `msgpack.unpackb(..., use_list=True)` + `tuple(refs)`? Does this preserve every byte and type required by existing index/validation/replay semantics, or does compatibility overhead erase it?

The simple control is the current `use_list=True` + CPython `tuple(refs)` on exactly the same binary payload. A no-freeze direct decode is an **unsafe performance floor**, never a valid correctness candidate. Tuple-first raw decoding without thaw is an explicit invalid-API negative control.

## Cheaper decisive evidence

1. First static compatibility audit: cite concrete current Reader and validation operations that require mutable lists (generation `append`, `sort`, row rename and `_validate_storage` list checks). Do not claim `use_list=False` is drop-in.
2. Then a source-bound, deterministic **micro/oracle** A/B on identical packed index bytes for N=4,096/65,536/262,144 refs, with at least two physical shape variants (constant and mixed valid blob lengths), independent child processes, paired ABBA ordering, CPU and wall ns, observed peak RSS and SHA-256. Generate payloads outside measured workers. Full object allocation after decode is charged. The tuple-first adapter may thaw only schema-required structural lists and MUST NOT walk or copy the large chunk reference tuple. Reject any altered value/byte, bogus source receipt or invalid shape. Include a negative recovery/delta-compatibility projection rather than inventing equivalent product semantics.
3. If micro survives, hosted exact-source Python 3.11 and optional three-host product court are separate gates; product credit is **not** assigned here.

**Promotion/falsification:** require tuple-first median CPU AND wall at least 5% better than freeze-after on both 65,536 and 262,144, semantic identity, and an economically credible path to support ordinary index, delta replay, preflight, optional ABI3 and hostile inputs. If any of these fail, **retire tuple-first as immediate shipping optimization**. Smaller isolated gains or correct shape reconstruction prove only a component hypothesis, not Reader compatibility.

**Alternative explanations:** `msgpack` tuple creation cost may exceed its later CPython copy; thawing structural arrays may recreate a larger total O(N) cost; decode semantics around journal operations and nested recipes may depend on list shapes; RSS high-water may be contaminated if fixture generation shares a process with measurements.

**Whole-system debt:** no claim for published Reader performance, recovery, malformed source safety, selective I/O, output archive bytes, 3-host native wheels, final RSS, packaging, version or release. Do not mutate benchmarks or lower exactness/security standards. No `docs/discovery/STATE.json` update unless a new decision-changing result exists.

## Prospective counterfactual

If static type/semantic constraints alone already rule out a drop-in, do not implement a shipping patch; measure only the bounded oracle needed to decide whether a *changed ownership boundary* offers enough headroom for a separate, explicitly compatible architecture. The next low-cost alternative is no new mechanism, retaining #676 as correctness seed with honest Q1 debt.

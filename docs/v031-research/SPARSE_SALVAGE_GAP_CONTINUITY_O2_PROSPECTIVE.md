# CMPCT v0.31 — Sparse SEEK_DATA discontinuity repair O2 (2026-10-23)

**Status:** prospective scientific-oracle repair only, not CMPCT product integration. Source parent: PR #296 head `6951d88518bc2cda8ab31af6577aac3ff4215b4c`, script blob `94fc2234df0035938be3151dfaa5eef7bc317598`, inherited bounded scanner blob `94c25029fdd167c00871aabbe8fe90fbe7490026`. Separate independent negative replication [PR #301](https://github.com/FCMO-AI/.CMPCT/pull/301) froze the split-magic question before its hosted execution; keep that negative historical baseline intact. No changes on other agent branches.

## Baseline and failure mechanism

The existing optional SEEK_DATA/SEEK_HOLE enumerator caches up to three bytes from each physically allocated extent for finding `CMA4` across adjacent *read windows*. It carries them into the next extent even when `start > cursor`, indicating an intervening logical-zero hole. It can therefore detect a split `CMA|4` assembled from disjoint regions, assign the false candidate to a position inside the hole, and `BHDR.unpack` proceeds without rechecking the magic that `pread` actually returned. The reference full logical scanner does not treat noncontiguous physical extents as adjacent.

Exploratory local reenactment had shown `CMA` ending one allocated page and `4` starting a later data extent produced a phantom offset with on-disk magic `00000034`. This is prior knowledge, not retroactively prospective O2 outcome.

## Frozen scientific prediction

A two-guard change to the existing research oracle, with no edit to CMPCT product:
1. clear `carry` *only* when SEEK_DATA advances past the previous logical extent stop (`start > cursor`); preserve it when extents are logically adjacent;
2. validate `header[:len(BMAGIC)] == BMAGIC` after a full logical `pread` before treating decoded fields as candidates.

On held-out Linux sparse files with physical holes and three split-magic prefixes (`CMA|4`, `CM|A4`, `C|MA4`), corrected `sparse_candidates(admit=False)` and admitted route must equal the authentic `recover_blob_records` full logical scan exactly, returning *only* an independently valid header from a third extent. Force unsupported fallback must still equal baseline. A real header whose initial magic is entirely in data and tail crosses into hole must still be discoverable. Original O0 4-case court must remain green with exact candidate fields/order; dense overhead stays negative, no performance win claim from this patch.

## Simpler controls and kill rule

The incumbent bounded scanner over the same physical file is the stronger semantic control. Adding only the `pread` magic check may block false publication even if cross-gap `carry` remains; adding only the carry reset may suffice for the observed case. Both inexpensive guards are selected for independent defense against future refactors and because the extra magic comparison uses already-read bytes. Their incremental cost on true candidates is constant, but end-to-end cost must be measured before productizing.

**Kill or narrow:** any positive phantom after patch, missing valid on-disk header, changed incumbent result, new resource unboundedness, false-accepting unsupported filesystem, or conflict with original O0 court means O2 cannot pass. On environments without *actually distinct extents* mark `UNSUPPORTED/NO DECISION` rather than claiming positive evidence.

## Evidence class and continuation

O2 is an engineering improvement to a **research oracle**, not a shipping scanner. Exact source fingerprints, independent hostile regressions and original O0 court must be tested via hosted Actions. Do not merge into released product or alter format, thresholds, frozen benchmarks, historical scoreboards, Discovery Engine policy or `STATE.json`. A prospective conversion into product requires multi-filesystem coverage and charged extent/resource/admission economics.

Counterfactual: the two-extent split-magic case is the cheaper must-have discriminating boundary than a test where a valid header's *tail* crosses a hole. Preserve both as complementary controls.

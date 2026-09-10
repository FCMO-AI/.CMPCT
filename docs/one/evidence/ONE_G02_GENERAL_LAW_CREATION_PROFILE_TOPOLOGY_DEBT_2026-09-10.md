# ONE-G0.2 general Law creation-profile topology debt — 2026-09-10

Status: **REGRESSION / EVIDENCE DEBT PRESERVED**

Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Finding

`ONE_G02_GENERAL_LAW_ARCHIVE_CREATION_PROFILE_PREREG_2026-09-10.md` freezes `mixed-8x512k` as an eight-file transfer case containing Surprise, exact reuse, ADD8, XOR, Fill, and unrelated content.

The current implementation in `benchmarks/one/one_g02_general_law_archive_creation_profile.py` constructs:

1. a Surprise base;
2. an exact copy;
3. an ADD8 target from that base;
4. an XOR target derived from the preceding ADD8 target;
5. Fill;
6-8. unrelated content.

The current product seam in `experiments/one/general_law_archive.py` deliberately rejects ADD8/XOR relation predictors whose selected predecessor is itself a Law root. Only a Surprise-backed predecessor is eligible for that promoted selective-safe relation topology. This prevents nested Law reconstruction from silently escaping the currently promoted selective-access lowering boundary.

Therefore the old `mixed-8x512k` fixture can contain XOR-related source bytes while failing to exercise an XOR Law root. A creation/RSS result from that row must not be described as performance evidence for the full preregistered Surprise + exact reuse + ADD8 + XOR + Fill mixture unless reader-side structure evidence proves otherwise.

## Consequence

Do not delete or rewrite historical result artifacts. Preserve any earlier measurements as evidence for the exact code/fixture that produced them, but narrow their interpretation: they cannot independently establish full mixed-Law creation cost if XOR was pruned.

This is not evidence that the selective-safe topology rule is wrong. The immediate repair is a new transfer profile that gives XOR an independent Surprise-backed source island while retaining eight files and all original performance thresholds. No Genesis input, comparator setting, or product semantic requirement may be changed to repair this debt.

## Genesis boundary

This finding was derived from transfer fixture/code inspection. The frozen 15 Genesis workloads were not generated, encoded, compared, scored, or inferred.

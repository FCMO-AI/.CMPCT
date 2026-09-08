# ONE-G0.2 lazy segment timing — pre-result hostile review

Date: 2026-09-08
Branch: `research/cmpct1`
Experimental line: ONE-G0.2

## Mission Lock

Hypothesis: moving the existing worst-case native `Segment * n` arena allocation until after relation admission can preserve admitted-path creation economics while producing a measurable creation-time improvement on rejected 1 MiB roots, complementing the already observed rejected-path peak-RSS reduction.

Frozen decision law is inherited unchanged from `ONE_G02_LAZY_SEGMENT_TIMING_PREREG_2026-09-08.md`:

- 1 MiB only;
- 21 paired alternating repetitions;
- admitted cases: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- rejected cases: `fragmented_every32`, `independent_random`;
- every admitted row must remain <=1.05x eager on both median wall and median CPU;
- every rejected row must reach <=0.95x eager on both median wall and median CPU;
- exact reconstruction/canonical-wire/relation semantics are mandatory;
- rejected lazy rows must allocate no Segment arena; admitted lazy rows must retain the same arena capacity as eager.

No threshold was changed during implementation or review.

## Builder boundary

The candidate changes only allocation scheduling:

- eager: allocate `(Segment * n)()` before relation admission;
- lazy: run the same admission first and allocate the same `(Segment * n)()` only when the relation is admitted.

Both arms then use the same native segmenter, bounded Law + Surprise Program construction, validation, and canonical growable emitter. Source/target ctypes conversion, native compilation, and root-digest preparation are common setup outside the paired timing interval. Decode/evaluation is semantic verification outside timing.

The allocator is tested exactly as the current writer uses it. The benchmark does not artificially touch all reserved pages. This matters because the prior RSS experiment already measures physical-memory consequences; page-touching here would turn the speed test into a different allocator policy.

## Hostile-review corrections before admissible result

### 1. Cross-arm result teardown contamination

The first implementation allowed Python loop/result ownership to survive into the next timing interval. Replacing the prior result could therefore destroy a large Program/wire/ctypes result after the next arm's clocks had started, charging teardown to the wrong candidate.

Correction: all owning references to the previous arm are released before both wall and CPU clocks start. The current result remains alive until both clocks stop. This mirrors the lifecycle lesson learned during the native-observer-boundary work.

Any timing collected before this correction is inadmissible for the lazy-segmentation speed decision.

### 2. Oracle objects retained during allocation timing

The semantic probe initially retained exact plan and canonical-wire objects through the 21-repeat timing loop. Since this experiment is specifically about large allocation scheduling, retaining MiB-scale oracle structures could alter allocator pressure and bias either arm.

Correction: eager/lazy probes first undergo full exact comparison of admission, plan, canonical wire, root digests, reconstruction, Surprise bytes and reader work. The heavy plan/wire objects are then released before timing, leaving only compact scalar metadata needed for the report.

Any timing collected while those heavy oracle objects remained live is inadmissible for the allocation-scheduling decision.

### 3. Decision-law reachability and vacuous promotion

The original pass/fail logic lived only at the end of `run()`. It did not independently prove that a single bad admitted row, a sub-5% rejected speedup, a rejected allocation, a semantic mismatch, or an incomplete matrix would block promotion.

Correction: the frozen law is extracted into `_adjudicate(rows, semantic_ok)` and covered by synthetic hostile tests. Tests require:

1. full green matrix -> `ADVANCE_LAZY_SEGMENT_TIMING`;
2. one admitted CPU ratio at 1.051 -> `HOLD_LAZY_SEGMENT_TIMING`;
3. one rejected wall ratio at 0.951 -> HOLD;
4. rejected row retaining any Segment allocation -> HOLD;
5. semantic failure despite green timing -> `INVALIDATE_LAZY_SEGMENT_TIMING`;
6. missing row -> HOLD, preventing vacuous `all()` promotion.

The exact-SHA workflow runs these decision-law tests before the expensive benchmark.

## Claim boundary

A positive result would establish a writer-internal scheduling improvement, not a new ONE representation mechanism. It would not by itself change stored bytes, decode semantics, selective-read amplification, reconstruction work, reader complexity, failure blast radius, or comparator standing against frozen v0.29/v0.30.

A negative timing result would not erase the existing resource evidence: rejected 1 MiB roots have already shown roughly 12.58 MB of avoided Segment arena and about a 26% fresh-process peak-RSS reduction, while admitted roots remain essentially unchanged. If the speed gate holds rather than advances, lazy allocation may remain useful as resource hardening, but it must not be sold as a creation-speed win.

## Exact evidence authority

Only an exact-source run after all three corrections above is admissible for the timing verdict. Earlier or superseded runs are implementation/debug evidence only.

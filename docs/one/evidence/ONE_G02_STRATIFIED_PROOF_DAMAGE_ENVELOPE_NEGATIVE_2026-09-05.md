# ONE-G0.2 — Stratified proof contiguous-damage envelope negative

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable negative evidence / claimed 16 KiB surviving-opportunity envelope retired  
**Result-bearing source:** `02358a5c7a794a65fe445b4cf712f7969d5a1ded`  
**Workflow:** `33961328979`  
**Job:** `101293608665`  
**Artifact:** `9968035073`  
**Artifact zip SHA-256:** `7e8005eb53446019391d838a2f79bcb8e24b0b2d8acb66c9637101bac82cab4e`

## Frozen question

After the stratified proof topology repaired the fixed-front 1 KiB contiguous-damage failure, this transfer asked a stronger causal question: for a 64 KiB source half followed by a globally +1-shifted target half, can the unchanged sixteen-stratum / four-exact-proof topology keep admitting every front, middle and tail contiguous-damage case while at least 16 KiB of full-minimizer marginal reuse survives?

The width grid was frozen before execution at 1, 4, 8, 16, 24, 32, 40, 48, 52, 56 and 60 KiB. The 16 KiB surviving-opportunity floor was also frozen. No proof count, shift set, coverage stride, majority rule or corpus placement may be changed inside this experiment after result.

## Exact result

`tests/one`: **76 passed**.

The experiment returned:

> `retire_16k_contiguous_damage_envelope`

The stratified exact-proof topology itself continued to work whenever the preceding coverage gate admitted the nominated shift. The first decisive failures occurred **before any exact proof attempt**.

### Boundary map

| Contiguous damage | Surviving marginal opportunity | Coverage result | Exact proofs | Admission |
| --- | ---: | --- | ---: | --- |
| 1 KiB | 64,511–64,512 B | strong +1 | 4 | all placements pass |
| 4 KiB | 61,439–61,440 B | strong +1 | 4 | all pass |
| 8 KiB | 57,343–57,344 B | strong +1 | 4 | all pass |
| 16 KiB | 49,151–49,152 B | strong +1 | 4 | all pass |
| 24 KiB | 40,959–40,960 B | +1 still above majority | 4 | all pass |
| 32 KiB | 32,767–32,768 B | +1 on majority boundary | 0 / 0 / 4 | front + middle fail; tail passes |
| 40 KiB | 24,575–24,576 B | +1 below majority | 0 | all fail |
| 48 KiB | 16,383–16,384 B | +1 well below majority | 0 | all fail |
| 52 KiB | 12,287–12,288 B | +1 below majority | 0 | all fail (outside frozen claimed floor) |
| 56 KiB | 8,191–8,192 B | +1 below majority | 0 | all fail (outside claimed floor) |
| 60 KiB | 2,048–4,096 B | +1 below majority | 0 | all fail (outside claimed floor) |

At 32 KiB damage, the source still contains about **32 KiB of real marginal exact reuse**, but front and middle placements have only 508 and 511 best-shift coverage hits respectively, so the frozen `best_hits * 2 < samples` prerequisite terminates before proof. Tail happens to land exactly at 512 hits and reaches four exact proofs.

At 40 KiB damage, all placements retain about **24.6 KiB** of real marginal reuse yet produce **zero proof attempts**. At the 48 KiB front placement, the full minimizer still has exactly **16,384 B** of marginal reuse—the frozen claimed floor—yet only 256 +1 coverage hits remain and proof is never attempted.

## Causal interpretation

This result does **not** falsify the newly successful stratified exact-proof topology. It exposes a different owner: the strict global coverage-majority prerequisite.

The gate currently requires both:

1. at least four one-byte support hits for the nominated displacement, and
2. support on at least half of all coverage samples,

before the exact proof stage can execute.

The first condition supplies a cheap lower bound on available distributed support. The second condition forces a global relation to dominate the entire relation length, even when tens of kilobytes of exact reusable structure survive. In this frozen corruption regime, that second condition is the recall limiter.

The earlier false-pattern transfer also matters: one-byte coverage alone is not sufficient because the every-32-byte fragmented adversary shows overwhelming +1 resemblance while containing **zero** minimizer marginal reuse. However, the stratified exact-proof stage independently rejects that adversary with **16 proof attempts and 0 exact proofs**. This creates a falsifiable new question: is global majority actually needed once exact distributed proof is mandatory, or is it redundant specificity that destroys recall?

## Scoped negative constraint

`global half-relation majority -> exact proof` is not sufficient as a complete admission architecture for partially damaged but materially reusable shifted relations. It loses cases with 16–32 KiB of real exact marginal opportunity in the tested 64 KiB relation regime.

This does **not** imply that every weaker coverage threshold is safe, nor that four one-byte hits alone are enough. Any superseding admission law must preserve exact proof, false-pattern rejection, bounded proof budget, compute/read ceilings and deterministic semantics.

## Reopening / superseding predicate

A superseding experiment may remove the majority prerequisite only if it is frozen as a new experiment and preserves:

- the same coverage stride and signed displacement set;
- at least the inherited four-hit nomination floor;
- sixteen deterministic proof strata;
- four exact 64-byte proofs for admission;
- maximum sixteen proof attempts;
- the every-32-byte fragmented false-positive control and every-96-byte positive control;
- random, compressed and zero negative controls;
- the same 5% incremental-selector compute ceiling and 25% modeled read ceiling;
- exact ONE reader-visible semantics.

Promotion must recover every row from this frozen damage matrix with at least 16 KiB of positive marginal opportunity while introducing no false admission in the inherited hostile matrix.

## Claim boundary

Writer-discovery research only. No ONE format, reader opcode, v0.29/v0.30 comparator, product performance or release authority changes.

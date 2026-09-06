# ONE-G0.2 relation witness proof deferral — hostile-review amendment

Date: 2026-09-06  
Activation T0: `2026-09-06T01:38:04Z` (environment clock; user timezone unavailable in this execution)  
Experimental line: `ONE-G0.2`  
Status: frozen before accepting result authority

## Why this amendment exists

The preregistered experiment isolates the **marginal pair-relation nomination cost** of the existing shared observer. The first implementation treated witness-first candidate nomination as terminal for relation-specific audition accounting, but allowed the baseline arm to continue charging later exact-reuse auditions/extensions after the baseline had already produced the first cross-object relation nomination.

That boundary was asymmetric. Work after the first relation nomination may still be useful to the independent exact-reuse discovery objective, but it is not marginal work required to answer the experiment's relation-nomination question. Charging that later work only to baseline could manufacture an exaggerated witness-first saving.

## Frozen correction

For both arms, relation-specific audition accounting stops after the **first pair nomination**:

- baseline pays exact witness verification plus exact-reuse extension required to reach its first qualifying cross-object nomination;
- candidate pays exact witness verification required to reach its first qualifying cross-object nomination and defers relation authority to the unchanged safe exact proof;
- both arms continue conceptually to permit the shared observer to serve its other discovery obligations, but later exact-reuse auditions are outside this marginal relation-nomination accounting experiment;
- when an arm nominates, it pays the same complete downstream safe-relation cost: sparse coverage comparisons plus exact-proof compared bytes;
- negative witness nominations remain fully charged to candidate even when safe proof rejects the Law.

The frozen decision thresholds from `ONE_G02_RELATION_WITNESS_PROOF_DEFERRAL_PREREG_2026-09-06.md` remain unchanged. This amendment makes the measurement boundary symmetric; it does not relax a gate.

## Authority rule

Any workflow/result from source before commit `2ff2563b5746817b04dbe68ae2c9bf7f607ffa0a` is methodologically superseded for this experiment, even if green. Result authority requires the corrected symmetric-accounting source or a descendant that does not change the frozen semantics/gates.

## Hostile-review claim boundary

A 64-byte witness remains only an Opportunity Gate. It never authorizes a reader-visible Law. The downstream exact safe relation proof remains the sole authority for relation emission. This is modeled proof-traffic evidence, not native elapsed-time or product-writer authority.
# ONE-G0.2 relation witness proof deferral — corrected terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2

## Authority

This result consumes the corrected symmetric accounting boundary frozen by `ONE_G02_RELATION_WITNESS_PROOF_DEFERRAL_HOSTILE_AMENDMENT_2026-09-06.md`. Any result from the pre-amendment harness remains superseded.

- branch head: `254fcc876dfd290d9653be0f1c4ac1e11b56d4c1`
- PR merge test SHA: `6b2702c2bf17deaecd6466d923c047a46ccfd10f`
- workflow run: `34004520029`
- result job: `101409197966`
- conclusion: **success**
- artifact: `9980565366`
- artifact SHA-256: `100513454b4f9a2f480cca2a08aead9a87101418248eb3f58f192ca1617905b0`
- ONE semantic/hostile suite: **93 passed**

## Result

The corrected candidate preserved every required relation opportunity and introduced no negative regression while reducing aggregate modeled relation-specific proof traffic from **4,104,106 B to 698,388 B**, or **0.170168x baseline** (about **82.98% less**).

Decision: **`advance_relation_witness_proof_deferral`**.

The gain is not uniform. On the hardest 256 KiB `fragmented_every96` rows the candidate is roughly **0.7185x** baseline proof traffic, showing that once safe exact proof dominates, witness deferral can eliminate only the speculative work ahead of that proof. This is a useful causal boundary, not a defect to tune away.

## Interpretation

A confirmed exact witness is valuable as an **Opportunity Gate**, not as semantic authority. It can cheaply justify running the safe exact relation proof while avoiding speculative exact-reuse extension work that the proof will supersede. The safe exact relation proof remains sole authority for emitting a Law.

This supports ONE's speed law: cheap evidence should decide whether expensive proof deserves to run. It does not add a reader operation or alter Law + Surprise representation.

## Claim boundary

This is controlled modeled/reference proof-traffic evidence. Python elapsed is not native writer-speed authority. The next promotion question is whether witness-first deferral survives inside the native fused nomination/admission path after charging event/index state, branches, nomination work, exact proof and negative controls.

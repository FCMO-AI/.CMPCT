# O71b — prospective matched-entropy independent-content falsifier

Date 2026-10-25 UTC. **Superseding/additional question, not a retrospective edit to O71.**

## Existing frozen evidence
Original source-exact O71 seven-case experiment [run #40179516645](https://github.com/FCMO-AI/.CMPCT/actions/runs/40179516645) / artifact #12593755705 / archive ZIP SHA-256 `24ba7b6019cbf7968ec94269ca6347e1362181b39f51e3348ce39c93e5601c8f` was decision-complete: shared mixed high-inflation ZIPs saved 34,779 complete bytes with VZIP versus opaque, while paying 15.25× create CPU. That observation **cannot be amended**. The O71 original scientific prereg, instrument and comparison remain identifiable by their original commits/blobs.

## New unresolved causal question
Did the shared mixed-entropy cohort win **because three ZIP members reconstructed exactly one 1-MiB raw SHA owner**, or could the same advantage appear in structurally equivalent ZIPs without any repeated raw SHA?

New held-out control: `independent_mixed_levels`, identical three genuine ZIP container names/member filenames/Deflate levels 1,6,9 and each expanded payload length 1 MiB, exact same construction logic, but payloads with **separately seeded small incompressible tails and separately patterned large low-entropy prefixes**. This deliberately destroys whole-raw equality while maintaining comparable compression-ratio/entropy class. No external files or source-code changes to product. One new paired arm gets three fresh-process repetitions per mode (6 new observations); O71 original seven cases remain measured as preserved replication (42 additional observations), and reporting distinguishes original O71 science from new O71b.

### Prospective prediction / falsifier
- Prediction: in the new independent-content mixed-entropy cohort, original O63 VZIP **will not** beat the same-input opaque oracle in full stored bytes, unlike `shared_mixed_levels` where −34,779 B was observed. This supports (but does not uniquely prove) exact-owner reuse as a principal mechanism.
- Falsify: if the independent-content control still beats opaque by >=128 complete bytes, the claim that exact SHA identity was the decisive cause is insufficient; explore partial structural reuse or compression-mode interactions. Preserve the negative or positive unchanged.
- Stronger control: the same workflow remeasures the original shared mixed case on the same runner and environment. Classify unmeasured library-level memory traffic, cross-host portability, or third-party ZIP/Zstd comparisons as pending.
- Kill/narrow: any mismatch of original source/codec/tree, non-equivalent ZIP semantics, product S_PACK routing, corrupted archives, fallback not reported, or source hash drift prevents a causal decision. Do not change threshold or metric to rescue result.

## Method / cost accounting
Keep O63 parent `18e32cae012f5dca9fc47f10d194f8b81005c85c`; product Builder `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`, codec `dc3446b0eed82edfba9380e3885a20aa45577899` unchanged. Real installed r24 Builder and Reader, identical physical tree in each AB arm, opaque only via inherited research interpreter fallback. Same fixed timestamps, SHA per source, two arms × three fresh subprocess observations, full archive bytes/CPU/wall/RSS/read/verify/extract and deterministic output SHA. Cross-family comparison must account for changes in ZIP physical bytes/levels/entropy rather than interpreting the shared-vs-independent size difference itself as same-input A/B; **within-family VZIP-vs-opaque is the valid causal A/B**. Source-identical O71b negative is evidence of the ownership boundary, not a universal predictor.

No release, code format, frozen benchmark, validator, or existing science outcome modification; O63, O68, O70 owners remain separate.
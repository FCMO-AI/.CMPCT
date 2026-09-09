# ONE-G0.2 block-cadence relation sketch — hostile review

1. **Fixed-grid alias must stay dead.** Lane positions are content-derived per block, but that alone does not prove alias resistance. The 24-cell semantic oracle is mandatory; any add8->XOR or other cross-family decision divergence invalidates the candidate.
2. **Block cadence can miss short/late relations.** This experiment does not claim arbitrary relation recall. It only asks whether the already-promoted coarse structural families survive with much cheaper carrying cost. Later transfer must add late/sparse/phase-shifted cases before discovery promotion.
3. **Extra memory traffic is real.** The candidate rereads a small number of bytes from the current/previous aligned blocks at chunk finalization. `source_scan_bytes==input` describes the forward scan, not all cache traffic. Therefore wall/CPU gates remain mandatory and ADVANCE must not be described as a memory-traffic proof.
4. **Fingerprint-derived lanes are writer-internal.** They are not reader semantics and may never authorize storage without exact proof.
5. **Global 7/8 agreement is intentionally conservative.** It can reject mixed-local relation structure; that is preferable to reopening a high-false-positive per-byte detector. Failure on a required positive is HOLD/INVALIDATE according to the frozen semantic law, not a reason to lower the threshold after observing CI.
6. **Synthetic families are mechanism evidence only.** An ADVANCE must next be integrated with exact span verification and measured as final information yield per CPU second on hostile/random/compressed/temporal transfer.
7. **No special-case suppression is admissible.** If an arithmetic ramp still aliases into XOR, do not add an `if add8: clear xor` patch. Change the sketch or evidence geometry.
8. **No hidden format change.** The experiment changes nomination only. ONE remains the same six-op Law + Surprise grammar.

# ONE-G0.2 hierarchy first-level fusion preregistration — 2026-09-06

Status: **preregistered diagnostic; not promotion authority**.

## Mission lock

The shared native writer already fuses ordinary one-level Segment plans directly into canonical concat refs. Only the `segment_count > ONE_MAX_NODES` hierarchy path still materializes a full `one_level_ref[segment_count]`, fills it from Segment metadata, rereads it in 4,096-ref chunks to emit first-level concat nodes, then discards it.

Hypothesis: for hierarchical plans, emitting the first hierarchy layer directly from the already-validated Segment buffer while materializing only the much smaller parent-ref array will preserve byte-identical canonical output and node numbering while materially reducing transient staging bytes and first-level elapsed.

This is causally different from rejected exact-capacity allocation. It does **not** precompute final wire size, change the output allocation policy, add a workload classifier, or alter reader semantics. It removes a derived metadata representation boundary.

## Referee / disproof

The local diagnostic is falsified if any of these occur:

1. seed/candidate hierarchy bytes differ;
2. canonical node numbering differs under mixed Ref/Surprise plans;
3. candidate transient hierarchy-ref storage is not lower on every tested hierarchical row;
4. median candidate/seed hierarchy-emission elapsed is greater than `0.80x`, or any tested row is above `1.00x` after equivalent warmup/order alternation;
5. the gain disappears when the candidate is charged for building the smaller parent array and counting first-level spans/surprise IDs.

This diagnostic cannot promote the mechanism into the shared native writer. A PASS only earns a full-writer A/B with the authoritative seed, exact semantic/wire oracle, resource accounting and hostile fragmented cases.

Do not rescue a FAIL using segment-count, corpus, density or surprise-rate thresholds. Hierarchical dispatch itself is already a canonical resource-bound consequence (`segment_count > ONE_MAX_NODES`), so testing this structural branch does not create a benchmark-derived heuristic.

## Frozen diagnostic shapes

Exercise at minimum:

- 4,097 all-Ref segments;
- 4,097 mixed segments with bounded Surprise count;
- 16,384 all-Ref segments;
- 65,536 mostly-Ref segments with Surprise count kept below the canonical node cap.

All shapes must have deterministic positive spans. The isolated boundary begins with validated Segment metadata and ends after writing the complete hierarchy concat bytes. Output allocation is pre-existing/equivalent and excluded equally from both arms; hierarchy-ref staging allocations are included.

Report per row:

- exact hierarchy bytes;
- seed transient `one_level_ref` bytes;
- candidate peak hierarchy-ref bytes;
- transient ratio;
- seed elapsed;
- candidate elapsed;
- candidate/seed elapsed ratio;
- parity status.

## Hostile-review question

A local win is only useful if it removes work that survives in the full native writer. Because hierarchy is uncommon and Surprise payload emission/root metadata may dominate full calls, the subsequent full-writer gate is mandatory before promotion.

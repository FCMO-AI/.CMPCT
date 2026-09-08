# ONE-G0.2 Lazy Segment Charged-Ingest Transfer — Hostile Review

**Date:** 2026-09-08  
**Experimental version:** `ONE-G0.2`

## Review target

Preregistration: `docs/one/prereg/ONE_G02_LAZY_SEGMENT_CHARGED_INGEST_PREREG_2026-09-08.md`  
Benchmark: `benchmarks/one/one_g02_lazy_segment_charged_ingest.py`

This review is pre-result for the charged-ingest transfer decision. It does not use a candidate timing outcome to change the gates.

## Mission lock

The experiment asks one question only: does the already-promoted lazy Segment-arena scheduling rule retain a useful timing advantage on reject paths when source/target ctypes conversion and root hashing are charged inside the same research-writer interval?

It is not a new representation experiment. Canonical Law + Surprise output, relation admission, segment plan, validation, direct final-buffer emission and reconstruction must remain identical between arms.

## Strongest attacks

### 1. Full ingest is still not actually charged

The widened interval includes Python bytes-to-ctypes conversion and SHA-256 of both roots, but excludes filesystem traversal, metadata capture, archive/index placement, native compilation/process startup and product integration. A pass is therefore evidence for the broader **research-writer envelope**, not total archive creation throughput.

**Disposition:** claim boundary is explicit in preregistration and JSON output. No product/CLI throughput claim is permitted from this lane.

### 2. Previous-root SHA-256 may be avoidable work in a versioned writer

The experiment deliberately hashes both previous and current roots. In a persistent adjacent-version writer, the previous root may already be authenticated/trusted state. Charging it can dilute the allocator benefit with work a mature writer need not repeat.

**Disposition:** this makes the falsifier harder, not easier, for the lazy scheduling delta. A pass remains useful. A hold does not prove lazy scheduling is unhelpful in a mature persistent writer; it means the local effect is diluted under this deliberately conservative bill. Future authentication fusion work must separate current-root hashing from redundant prior-root rehashing before making architectural conclusions.

### 3. ctypes conversion duplicates source bytes before native segmentation

Both arms pay two `from_buffer_copy` conversions. This is current research-boundary cost, not an ideal zero-copy native ingest architecture.

**Disposition:** identical cost is intentionally charged to test transfer. Do not conclude that conversion itself is acceptable or canonical. Compact/zero-copy ingest remains separate debt.

### 4. Arena capacity is a modeled resource measure, not peak RSS

The benchmark records eager/lazy Segment capacity but does not execute each repetition in a fresh subprocess to measure peak RSS. The earlier resource experiment is the actual RSS authority.

**Disposition:** no new peak-RSS claim is permitted from this timing lane. The prior ~26% reject-path fresh-process peak-RSS reduction remains separate evidence.

### 5. Allocator history can contaminate an allocation-scheduling microeffect

Repeated alternating arms share one process and allocator state. The lazy arm could benefit or suffer from pages/arenas touched by the eager arm.

**Disposition:** paired A/B-B/A ordering reduces directional drift, but does not make allocator state independent. The test therefore uses a modest 3% reject-path transfer gate rather than attempting to reproduce the local 5% threshold under a much larger charged envelope. Fresh-process RSS remains separate. If timing lands near the gate, treat the result as sensitive and repeat on another runner before product promotion.

### 6. The 64 KiB rows could hide fixed overhead

At small scales allocator scheduling may be below timer noise while conversion/hash overhead dominates.

**Disposition:** 64 KiB rows cannot advance the mechanism. They only veto gross regression at 1.08x. The 1 MiB matrix is the decision scale.

### 7. Benchmark object lifetime can leak teardown into the next arm

This class of error has already occurred in prior ONE timing work.

**Inspection:** the timed loop clears the prior owning `value` before starting either clock, stores the new result until both clocks stop, and semantic probes release heavy results before timing. This preserves the previously learned lifecycle discipline.

### 8. Decision code could advance on an incomplete matrix

**Inspection:** `_adjudicate` constructs the exact expected `(size, case)` key set and requires exact equality before any gate can pass. Synthetic tests explicitly prove a missing row produces HOLD.

### 9. A timing win could conceal semantic drift

**Inspection:** eager/lazy probes require equivalent native plan, canonical wire/stats, admission, SHA roots and exact reconstruction through `_semantic_signature`; rejected lazy capacity must be zero and admitted capacity must equal eager. Semantic failure forces INVALIDATE regardless of timing.

## Frozen verdict contract

No threshold changes are authorized after result consumption:

- admitted 1 MiB rows: wall and CPU <= 1.05x;
- rejected 1 MiB rows: wall and CPU <= 0.97x;
- every 64 KiB row: wall and CPU <= 1.08x;
- exact semantics mandatory;
- complete matrix mandatory.

## Review conclusion

The experiment is admissible as a **transfer falsifier** for lazy Segment scheduling under a wider charged research-writer boundary.

A pass supports promoting lazy allocation across that research writer. A hold preserves the already-proven local timing and resource results but does not authorize claiming a broader ingest-speed gain. An invalid semantic result kills the candidate.

The strongest unresolved system debt after either pass or hold remains the same: remove avoidable Python/native copying/materialization and measure the eventual writer at product-scale wall/CPU/RSS boundaries rather than endlessly optimizing isolated stages.

# ONE-G0.2 fused nomination bounded demand-grown index — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: preregistered; execute only if the fused carrying-cost gate does not retire the hot-path principle

## Mission Lock

The exact fused semantic prototype reserves 64 local entries plus the entire 8,192-entry global hard cap up front. With the research struct layout (`24 B/entry`) that is 198,144 B of writer-side event-index storage. This is a representation/allocation artifact, not a semantic requirement.

The terminal 90-row fused result observed the local cap of 64 as expected but at most 272 live global entries, meaning only 8,064 B of entries were actually live at the worst observed point. The fixed reservation is therefore roughly 24.6x the live-entry footprint on that envelope.

## Falsifiable hypothesis

The global first-witness index can preserve exactly the same 8,192-entry hard cap and lookup/insertion semantics while allocating capacity on demand in bounded geometric steps. This should remove most ordinary resident-state debt without changing nomination outcomes or introducing a new discovery mechanism.

## Candidate shape

- local FIFO remains the same fixed 64-entry structure;
- global index starts at 64 entries on first use;
- capacity doubles only when required: 64 -> 128 -> 256 -> 512 -> ... -> 8192;
- growth never exceeds the existing 8,192-entry semantic cap;
- all existing entries remain in the same logical insertion order;
- allocation failure is explicit failure, never silent semantic fallback;
- no reader-visible state or format change.

This prereg does not authorize lowering the global cap to fit the current corpus.

## Frozen semantic/resource gate

Replay the terminal 90-row fused envelope and require:

- selector trace/state exact;
- cross auditions/exact nominations exact;
- false exact nominations = 0;
- same local/global peak *entry counts* as the fixed prototype;
- actual allocated global capacity >= live entries and <= 8192;
- demand-grown event-index reserved bytes <= fixed prototype bytes on every row;
- at 256 KiB relation size, maximum demand-grown event-index reservation <= **16,896 B** (64 local + at most 640? implementation must report exact capacity; the bound intentionally allows a 512-entry global power-of-two capacity plus allocator/layout slack only when explicitly modeled).

If the implementation reports entry-array bytes directly with 24-byte entries and 512 global capacity, the expected exact array reservation is 13,824 B (`(64+512)*24`).

## Decision law

- `advance_bounded_demand_nomination_index`: all semantic gates exact and state reservation materially reduced;
- `repair_bounded_demand_nomination_index`: any semantic mismatch or cap/accounting error;
- `retire_state_rehabilitation`: only if preserving semantics unexpectedly requires effectively max-resident allocation or unacceptable allocation/control complexity.

## Hostile Reviewer

Demand growth can trade resident memory for allocator calls, copying, and branch work. Passing this gate proves memory rehabilitation only. A later paired timing gate must include growth/reallocation cost and cannot borrow the fixed prototype's elapsed result. If realloc/copy cost is material, pre-sizing from an already-known safe upper bound or a compact arena may be preferable, but no solution may silently allocate the full maximum again and call itself demand-grown.

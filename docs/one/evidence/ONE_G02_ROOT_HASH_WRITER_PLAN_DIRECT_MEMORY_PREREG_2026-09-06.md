# ONE-G0.2 root-hash writer plan-direct creator-memory preregistration — 2026-09-06

## Mission lock

The exact-source V2 plan-direct writer (`71c0ecc45a4d3b96e689549ad7912046465d404d`) passed byte-identical canonical semantics and improved mature writer elapsed to `0.7807797801x`, but that run intentionally made no peak-memory claim.

This independent lane measures **creator-side Python traced peak allocation only** for the authoritative Program-materializing baseline versus the semantically identical V2 direct-plan compiler. It does not measure total process RSS, native C allocations, decoder memory, or system memory bandwidth, and it has no speed-promotion authority.

## Falsifiable hypothesis

Removing Python `Program` / `Node` / `Ref` materialization materially lowers creator-side peak Python allocation on the same frozen temporal matrix while preserving byte-identical ONE0 output.

## Disproof / acceptance

Semantic mismatch invalidates the lane.

For the mature productive range (64/128/256 KiB), accept the bounded memory claim only if:

- median candidate/baseline traced-peak ratio `<= 0.80x`;
- no mature productive row exceeds `1.03x`;
- candidate median absolute saving is at least `32 KiB`;
- mature control median is `<= 1.03x` and no mature control row exceeds `1.08x`.

Otherwise record a negative; do not reinterpret the V2 speed result as a memory win.

## Frozen method

- Matrix: the same 4/8/16/32/64/128/256 KiB productive/control cases used by the root-hash writer V2.
- Nine independent allocation samples per arm/row.
- Before each sample: `gc.collect()`; then `tracemalloc.start()`; execute exactly one writer call; read `tracemalloc.get_traced_memory()[1]`; stop tracing and drop the returned value before the next sample.
- Alternate A/B and B/A order by sample index.
- Report medians.
- Re-run byte/stats/admission/plan/traffic/segment/depth/node-count equivalence and decode/evaluate exactness before allocation sampling.
- Full `tests/one` must remain green.

`tracemalloc` instrumentation is deliberately not used for elapsed claims. Its measurement overhead is irrelevant to this lane because only peak traced allocation is compared.

## Scope boundary

A positive result establishes only reduced **Python allocator peak** for creator-side writer compilation. It does not establish lower RSS or native peak memory. If positive and materially useful, a later process-level RSS/native resource lane may test the broader claim.

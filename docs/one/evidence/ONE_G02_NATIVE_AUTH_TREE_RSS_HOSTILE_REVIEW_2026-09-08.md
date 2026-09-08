# ONE-G0.2 native AuthTree packed-state RSS — pre-result hostile review

Date: 2026-09-08
Status: preregistered, pre-result
Experimental version: `ONE-G0.2`

## Mission / claim discipline

This lane asks whether the newly advanced packed native AuthTree construction shape transfers without a peak-memory regression against the current Python reference tree. It is deliberately separate from prior SHA throughput work and from the queued packed-range-proof latency lane.

## Material flaw found before result: source-generation high-water contamination

The first benchmark draft used `random.Random(...).randbytes(size)` before recording the pre-tree RSS watermark. CPython may implement a large `randbytes` request through a source-sized `getrandbits()` integer and conversion, creating a transient object larger than the retained source bytes. Because `ru_maxrss` is a historical high-water mark, that temporary could raise the baseline before either tree was constructed and artificially shrink both measured incremental tree-RSS deltas.

No result from that draft is admissible.

The corrected frozen source is a deterministic 4 KiB byte block repeated directly to the exact 4 MiB / 16 MiB root size. The frozen sizes are block-aligned, so this creates one retained source object without a source-sized temporary integer/list. Thresholds, leaf widths, repetitions and decision law were not changed.

## Surviving limitations

1. **Linux-only accounting.** Hosted `ru_maxrss` is interpreted as KiB. This is not a portable allocator/memory contract.
2. **High-water deltas, not live heap attribution.** `after-before` means additional process peak above the source/import watermark. It includes allocator/library effects triggered by tree creation but cannot assign them object-by-object.
3. **Current native handoff is charged.** `build_auth_tree_native()` allocates a ctypes output arena and then copies it into returned Python `bytes`; these can coexist transiently. The benchmark intentionally does not hide that duplication.
4. **Native compiler child is not charged to RUSAGE_SELF.** The research wrapper compiles its shared library in a subprocess on first use. Compiler RSS is outside the Python child’s self RSS. This lane is about steady writer-process tree-state construction, not build-tool memory or startup latency. Product integration must prebuild the native component rather than invoke a compiler in the writer.
5. **Reference Python graph is a research control.** A green result means packed state is better than the current materialized Python `AuthTree`, not that its memory layout is globally optimal.
6. **Logical storage equality is not RSS equality.** Both arms must report the same authenticated node count and logical `stored_index_bytes`; process memory may differ because Python object headers, allocator arenas, ctypes buffers and shared-library pages are implementation costs.
7. **Zero incremental median invalidates.** If source/import history masks the tree increment at the measurement resolution, the decision must not exploit a zero denominator or call the candidate free.

## Cross-evidence reconciliation

Existing multi-buffer SHA evidence is not duplicated here. The elapsed-only multi-buffer seed showed a real hashing gain, but the later resource/crossover falsifier rejected its tested node-count dispatch because every raw candidate row lost on both wall and CPU while staging ~1.86 source-equivalents at large 112-byte-leaf roots and carrying 56,064 B extra explicit workspace.

The new native scalar/packed builder therefore advances a different principle: remove Python construction/object overhead and keep proof-capable node state compact. This RSS lane decides whether that representation shape also earns its process-memory cost. It makes no claim to be the fastest cryptographic kernel.

## Frozen interpretation

- `ADVANCE_NATIVE_AUTH_TREE_RSS`: exact semantics/accounting and large-root peak-RSS gates pass; packed native state is preferred over the Python materialized tree for the research sidecar, subject to proof/integration/portability gates.
- `HOLD_NATIVE_AUTH_TREE_RSS`: preserve the native creation-speed result, but treat the current ctypes-to-bytes handoff or packed-state lifetime as memory debt before promotion.
- `INVALIDATE_NATIVE_AUTH_TREE_RSS`: measurement resolution, matrix completeness, or semantic/accounting equality failed; no resource conclusion.

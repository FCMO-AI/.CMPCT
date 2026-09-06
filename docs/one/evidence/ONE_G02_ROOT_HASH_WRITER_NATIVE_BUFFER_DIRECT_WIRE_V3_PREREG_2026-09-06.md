# ONE-G0.2 root-hash writer native-buffer direct-wire V3 — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

The promoted plan-direct V2 compiler removes Python `Program`/`Node`/`Ref` materialization and yields mature productive writer elapsed `0.7807797801x`, but it still performs an intermediate conversion:

`native segment buffer -> Python tuple plan (+ copied Surprise payload bytes) -> canonical wire`.

The improved writer attribution localized the broad segment phase as the largest measured writer owner at `35.1295%` median share. Independent sub-attribution is running to separate native-kernel from Python plan-marshalling cost; this lane does not wait on that result because the intermediate plan is independently removable and byte-equivalence is directly falsifiable.

## Falsifiable hypothesis

Compiling canonical ONE0 directly from the authoritative native segment buffer, while preserving the exact scalar segment kernel and exact canonical hierarchy policy, materially improves the full root-hash-charged V2 writer by eliminating Python tuple-plan construction and per-Surprise payload copies.

This is compiler fusion only. It may not alter any segment boundary, Law/Surprise choice, canonical node ordering, hierarchy, Ref field, root, stored byte or reader behavior.

## Frozen Builder design

Baseline is the exact current plan-direct V2 path:

`root hashes -> admission -> scalar native segment buffer -> _native_plan tuple/payload marshalling -> _direct_wire_from_plan_v2`.

Candidate:

`root hashes -> identical admission -> identical scalar native segment buffer -> direct canonical wire from seg_buf + target`.

Candidate requirements:

- do not construct the tuple `plan`;
- do not materialize Surprise payload `bytes` before canonical emission; emit target spans from a `memoryview`/buffer directly into the output bytearray;
- validate every native segment kind/start/length and exact target coverage;
- preserve V2's creator-known span vs serialized `Ref.length` distinction for intermediate concat hierarchy;
- preserve canonical node numbering: source Surprise node first, then target Surprise nodes in segment order, then intermediate concat nodes, then final concat;
- preserve exact lexical root order and SHA-256 values;
- disabled relation remains source Surprise + target Surprise exactly as V2;
- no new reader-visible operation or wire field.

The candidate may keep lightweight creator-only `(node,start,wire_len,span)` reference bookkeeping required for bounded hierarchy construction. The measured claim is elimination of the tuple plan and copied Surprise payload objects, not zero Python allocation.

## Frozen matrix and semantic authority

Use the exact V2 relation generator, productive/control cases, sizes and 31-round paired A/B–B/A timing contract.

Before timing every row require:

- baseline and candidate canonical bytes exactly equal;
- WireStats exactly equal;
- admission enable, best shift, exact-proof count and gate traffic equal;
- scalar native segment count/traffic equal;
- native segment buffer converted only for audit must match the independent Python segmentation oracle;
- hierarchy depth and node count equal;
- decoded/evaluated outputs exactly equal source/target roots.

Add malformed native-buffer probes for zero length, out-of-range source Ref, out-of-range Surprise target span, unknown kind, incomplete/over coverage and excessive segment count. Failure to reject invalid input invalidates the lane.

## Frozen performance gates

Over mature productive rows (16/32/64/128/256 KiB):

- median candidate/baseline full-writer elapsed `<=0.90x`;
- at least 12 mature productive rows `<=0.95x`;
- no mature productive row `>1.03x`;
- mature control median `<=1.03x`;
- no mature control row `>1.08x`.

If the candidate misses the whole-writer gate, preserve the negative even if plan-marshalling attribution later shows a large local share. Do not rescue it with plan-density or size thresholds.

## Resource and claim boundary

Record canonical bytes, Surprise bytes, segment count, hierarchy depth, node count, reader work and reader materialization. This lane does not establish process RSS/native allocation, arbitrary/fused discovery performance, filesystem durability, cross-platform portability, or v0.29/v0.30 supremacy.

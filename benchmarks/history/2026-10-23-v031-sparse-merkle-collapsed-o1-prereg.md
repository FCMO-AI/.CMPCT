# v0.31 — O1 Collapsed Sparse Merkle: frozen pre-result court

**Preregistered:** 2026-10-23 UTC. **Exact research base:** PR #276 `5f7ed18e900240ca7f288c962066ad32f92c44da`. **Owner:** phased1 O1 compact-tree research only. **Format:** revision 24 remains unchanged.

## Primary question and evidence tier
Can we *exactly preserve the O0 experimental Merkle root and member proof semantics* without materializing `ceil(logical_size/leaf_size)` leaf nodes, including a 1 TiB sparse logical file? This is **O1 standalone representation/proof research**, NOT a CMPCT Reader, Builder, released archive or compatibility claim. The r24 conventional flat SHA-256 remains authoritative and *different*.

## Falsifiable prediction
An independently coded collapsed-subtree implementation with O0 `SHA256(b'L'+len_4+leaf)`, `SHA256(b'N'+left+right)`, PAD `SHA256(b'P:missing')`, and `SHA256(b'F'+size_8+leaf_4+top)` should:
1. Match a separately implemented full-materialization reference for >=300 deterministic diverse small files, including odd leaf counts, empty files, partial tails and interval shifts.
2. Materialize a 1 TiB logical archive model with two nonempty 64 KiB leaves, cold-serialize/reopen its charged descriptor using **128 bytes** (`48+40*2`), peak Python tracemalloc **<5 MiB**, **<300** collapsed cache nodes per side, and no O(logical leaf-count) enumeration.
3. Produce and independently verify 64 KiB member proofs for first, last and touched leaves, rejecting mutated payload, sibling digest, root, length, duplicate/out-of-order index, and out-of-bounds offsets.
4. Include a negative control: dense/fragmented data still carries `48+40*k` index bytes and cannot earn generic economic credit.

## Controls and kill/narrow
Strongest simpler control = O0 full-leaf-array Merkle reference in PR #276; its semantics are authority for this research root but not r24 semantics. A flattened/fully materialized array is acceptable only for bounded small differential tests, never the 1 TiB scenario. Kill O1 proof claim for *any* root/proof mismatch, hidden positional fact not in charged rows, accepted hostile descriptor, unbounded 1 TiB memory/latency, or mutated frozen O0 comparator. Alternative explanation: speed may simply be cached leaf hashes while proof/index reconstruction still scales O(n); measure cold reopen and visited nodes to falsify it.

## Accounting and uncertainty
Descriptor is a standalone hypothetical fixed 48-byte `magic4 + logical size8 + leaf size4 + root32` plus one sorted 40-byte `index8 + digest32` record per touched leaf. All extents and byte placements are **gifted** by model generator; no generic admission, physical filesystem semantics, extractor I/O, source scanning, native ABI, recovery or authentication trust anchor are measured. Python tracemalloc does not capture all process RSS. A descriptor/root pair can be forged together; this model gives internal consistency, not origin authentication. Fully charged product bytes require additional evidence.

## Concurrency
PR #276 owns O0 measured economics. PR #255/#270/#273 own sparse product and cost attribution, PR #274/#277 own opt-in RAW selective verification; do not edit them. This O1 branch is based on PR #276 and will add only a new research script and exact-head workflow. `docs/discovery/STATE.json` is a staleable shared cache and remains untouched.

## Decision
Proceed to O2 product-level design only if full roots/proofs match the independent oracle, hostile controls fail closed, O(occupied leaves * log(logical leaves)) memory/work remains bounded, and complete index bytes are exposed. Otherwise narrow or retire. Never weaken r24 SHA, evaluator or release gate.
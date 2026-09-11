# ONE-G0.2 compact validation certificate V2 — result

Date: 2026-09-09  
Decision: **REJECT_V2_BEFORE_FALSIFIER**

## Exact execution authority

- Source: `18c3d2d5a1c9c3883ff3ac3b55c0c6da804d7eb6`
- Workflow: `CMPCT1 ONE-G0.2 compact validation certificate`
- Run: `34393996548`
- Job: `102609038481`

The exact-source lane did **not** reach the frozen benchmark. It failed an inherited retained-state test after 44 other validation/range tests passed. No benchmark artifact exists, so this lineage is not admissible promotion evidence.

## Failure

V2 replaced per-index `Struct('<Q').unpack_from(...)[0]` with a read-only `memoryview(...).cast('Q')` on little-endian machines. That removes a tuple-producing decode from the hot lookup path, but the view object itself has resident Python overhead.

On the small inherited `xor_crack` validation case, measured retained preflight state became:

- ordinary certificate: **304 B**
- V2 packed certificate: **369 B**

The test correctly rejected `369 < 304` as false.

This is not a reason to hide the view object's memory, change the accounting model, or relax the V1 gate. It shows that a packed certificate has a fixed metadata cost and should not be installed when it does not actually reduce retained state.

## Causal rehabilitation

The next candidate may reopen this line only with an **economic admission rule derived from the representations themselves**, not a benchmark-size threshold:

1. run the exact ordinary full validation first;
2. build the compact candidate only when all proven lengths fit the uint64 optimization domain;
3. compare the honest retained Python state of compact vs ordinary proof representation;
4. retain the compact representation only when it is strictly smaller; otherwise preserve the ordinary authority.

This makes tiny graphs pay neither the compact memory tax nor its lookup overhead, while large graphs can retain the ~0.223x V1 memory result. The frozen V1 scientific matrix and CPU/memory gates remain unchanged.

No ONE wire or semantic change is authorized by this result.

# ONE-G0.2 Native Plan Bulk — preregistration

## Mission lock

`ADVANCE_GENERIC_EXECUTION_PLAN` established a reusable six-op reader-internal control plane. At 1 MiB, graph-heavy composition improves while XOR/add8 remain ~1.00x because Python byte arithmetic dominates. Test the next causal boundary without changing the Program or adding opcodes.

## Hypothesis

Keeping the exact prepared plan, Python ref slicing/work accounting, root SHA-256 and all non-arithmetic operations unchanged, moving only the existing XOR/add8 byte loops to a bounded C11 kernel will materially reduce arithmetic replay time while remaining neutral on the four non-arithmetic families.

## Disproof

The hypothesis is false in this shape if any XOR/add8 cell across 64 KiB / 256 KiB / 1 MiB exceeds 0.35x generic-plan median wall or CPU, or if any non-arithmetic cell exceeds 1.05x. Semantic/work disagreement invalidates rather than holds.

## Frozen matrix / timing

Same 18 cells as the generic-plan experiment: three sizes x terminal_mix, repeat, slice_concat, xor2, add8_3, shared_basis. Nine paired alternating repetitions. The native research library is warmed before timing; shared-library compilation/startup is not a product claim and would not exist as runtime compilation in a built reader.

Inputs to the native arithmetic kernel are the same Python slice bytes already created/charged by the generic plan. The ctypes boundary uses pointers to those immutable bytes and does not pre-copy input payloads. Candidate output allocation/freeze remains charged.

## Invariants

- same six reader-visible operations;
- same Program and roots;
- exact output bytes and SHA-256 root verification;
- identical reference work accounting;
- no corpus/workload dispatcher;
- no weakening of limits, depth, range or integrity semantics;
- non-arithmetic execution remains the same algorithmic shape.

## Decision

`INVALIDATE_NATIVE_PLAN_BULK` on semantic/work disagreement or incomplete/duplicate matrix.

`ADVANCE_NATIVE_PLAN_BULK` only if all six arithmetic cells are <=0.35x generic plan on both median wall and CPU and every non-arithmetic cell is <=1.05x.

Otherwise `HOLD_NATIVE_PLAN_BULK`.

## Claim boundary

Hosted Linux/CPython/C11 hot-replay evidence only. No startup, RSS, selective-range, wire, portability or canonical-backend claim. A green result establishes a data-plane implementation opportunity for existing Law operations, not a new representation mechanism.
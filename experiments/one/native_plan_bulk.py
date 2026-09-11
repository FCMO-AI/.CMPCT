"""ONE-G0.2 native bulk data plane for the generic prepared execution plan.

Only the already-canonical xor/add8 byte arithmetic moves to C. Ref slicing, work charging,
all other operations, root materialization and SHA-256 remain structurally equivalent to
`generic_execution_plan.execute_plan`, so the falsifier isolates bulk arithmetic cost.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from experiments.one.generic_execution_plan import GenericExecutionPlan, PlanRef, PlanStats
from experiments.one.ir import OneError

_U8P = ctypes.POINTER(ctypes.c_uint8)


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("native_plan_bulk_kernel.c")
    build_dir = Path(tempfile.mkdtemp(prefix="cmpct-one-plan-bulk-"))
    output = build_dir / "libone_plan_bulk.so"
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    for name in ("one_plan_xor_many", "one_plan_add8_many"):
        fn = getattr(lib, name)
        fn.argtypes = [_U8P, ctypes.POINTER(_U8P), ctypes.c_size_t, ctypes.c_size_t]
        fn.restype = ctypes.c_int
    return lib


def _bulk_equal(op: str, pieces: list[bytes]) -> bytes:
    if op not in {"xor", "add8"}:
        raise OneError(f"unknown native bulk operation {op!r}")
    if len(pieces) < 2 or len(pieces) > 9:
        raise OneError(f"native {op} operand count outside bounded kernel")
    width = len(pieces[0])
    if any(len(piece) != width for piece in pieces[1:]):
        raise OneError(f"{op} operands differ in length")
    if width == 0:
        return b""

    # c_char_p keeps each immutable Python bytes object alive and passes its existing
    # contiguous payload address. No from_buffer_copy is used for input operands.
    keepers = [ctypes.c_char_p(piece) for piece in pieces]
    pointers = (_U8P * len(keepers))(*(ctypes.cast(item, _U8P) for item in keepers))
    sink = bytearray(width)
    sink_view = (ctypes.c_uint8 * width).from_buffer(sink)
    fn = _library().one_plan_xor_many if op == "xor" else _library().one_plan_add8_many
    rc = fn(ctypes.cast(sink_view, _U8P), pointers, len(pieces), width)
    if rc != 0:
        raise OneError(f"native {op} kernel rejected with status {rc}")
    return bytes(sink)


def execute_native_bulk_plan(plan: GenericExecutionPlan) -> tuple[dict[str, bytes], PlanStats]:
    values: dict[int, bytes] = {}
    work = 0

    def charge(amount: int) -> None:
        nonlocal work
        if amount < 0:
            raise OneError("negative native-plan work charge")
        work += amount
        if work > plan.max_work_bytes:
            raise OneError("native-plan work exceeds declared limit")

    def part(ref: PlanRef) -> bytes:
        source = values[ref.node]
        out = source[ref.start : ref.start + ref.length]
        if len(out) != ref.length:
            raise OneError("native-plan range mismatch")
        charge(len(out))
        return out

    for item in plan.ops:
        if item.op == "surprise":
            result = bytes(item.surprise)
            charge(len(result))
        elif item.op == "fill":
            result = bytes([item.value]) * item.count
            charge(item.count)
        elif item.op == "concat":
            pieces = [part(ref) for ref in item.refs]
            if item.surprise:
                pieces.append(item.surprise)
                charge(len(item.surprise))
            result = b"".join(pieces)
            charge(len(result))
        elif item.op == "repeat":
            source = part(item.refs[0])
            result = source * item.count
            charge(len(result))
        elif item.op in {"xor", "add8"}:
            pieces = [part(ref) for ref in item.refs]
            if item.surprise:
                pieces.append(item.surprise)
                charge(len(item.surprise))
            result = _bulk_equal(item.op, pieces)
            charge(len(result) * len(pieces))
        else:
            raise OneError(f"unknown planned operation {item.op!r}")

        if len(result) != item.length:
            raise OneError("native-plan output length disagrees with preflight")
        values[item.node] = result

    outputs: dict[str, bytes] = {}
    for root in plan.roots:
        source = values[root.node]
        value = source[root.start : root.start + root.length]
        if len(value) != root.length:
            raise OneError(f"root {root.name!r} length mismatch")
        charge(len(value))
        charge(len(value))
        if sha256(value).hexdigest() != root.sha256_hex:
            raise OneError(f"root {root.name!r} sha256 mismatch")
        outputs[root.name] = value

    if work > plan.preflight_worst_work_bytes:
        raise OneError("native-plan runtime work exceeded preflight upper bound")
    return outputs, PlanStats(sum(len(value) for value in values.values()), work, len(values), len(outputs))

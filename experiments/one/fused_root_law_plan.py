"""ONE-G0.2 bounded root Law fusion for the existing generic execution plan.

This is a reader-internal execution lowering, not a reader-visible operation. It accepts
only a full root Concat whose children are either direct Surprise spans or existing
add8/xor nodes with one Surprise operand plus one uniform Fill operand. Compatible cones
are written directly into final root positions through one bounded native invocation.
Unsupported shapes fail closed to the caller; there is no fallback inside this module.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from experiments.one.generic_execution_plan import GenericExecutionPlan, PlanOp
from experiments.one.ir import OneError

_U8P = ctypes.POINTER(ctypes.c_uint8)


class _Cmd(ctypes.Structure):
    _fields_ = [
        ("src", _U8P),
        ("dst", ctypes.c_size_t),
        ("len", ctypes.c_size_t),
        ("value", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
    ]


@dataclass(frozen=True)
class FusedRootLawPlan:
    root_name: str
    root_length: int
    root_sha256: str
    commands: object
    keepers: tuple[ctypes.c_char_p, ...]
    command_count: int
    stored_source_bytes: int
    derived_bytes: int
    modeled_traffic_bytes: int


@dataclass(frozen=True)
class FusedRootLawStats:
    root_bytes: int
    command_count: int
    stored_source_bytes: int
    derived_bytes: int
    modeled_traffic_bytes: int


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("fused_root_law_plan_kernel.c")
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-root-law-fusion-"))
    output = build / "libone_root_law_fusion.so"
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_execute_root_law_plan
    fn.argtypes = [_U8P, ctypes.c_size_t, ctypes.POINTER(_Cmd), ctypes.c_size_t]
    fn.restype = ctypes.c_int
    return lib


def _full_ref(ref, op: PlanOp) -> bool:
    return ref.start == 0 and ref.length == op.length


def compile_fused_root_law_plan(plan: GenericExecutionPlan) -> FusedRootLawPlan:
    if len(plan.roots) != 1:
        raise OneError("root Law fusion requires exactly one root")
    root = plan.roots[0]
    by_node = {item.node: item for item in plan.ops}
    root_op = by_node.get(root.node)
    if root_op is None or root_op.op != "concat" or root.start != 0 or root.length != root_op.length or root_op.surprise:
        raise OneError("root Law fusion requires one full root concat")

    specs: list[tuple[int, bytes, int, int]] = []  # kind, source, value, length
    offset = 0
    stored_source_bytes = 0
    derived_bytes = 0

    for root_ref in root_op.refs:
        child = by_node.get(root_ref.node)
        if child is None or not _full_ref(root_ref, child):
            raise OneError("root Law fusion requires full child refs")
        if child.op == "surprise" and not child.refs and child.length == len(child.surprise):
            specs.append((0, child.surprise, 0, child.length))
            stored_source_bytes += child.length
            offset += child.length
            continue
        if child.op not in {"xor", "add8"} or child.surprise or len(child.refs) != 2:
            raise OneError("unsupported root Law child")

        operands = [by_node.get(ref.node) for ref in child.refs]
        if any(op is None for op in operands):
            raise OneError("missing root Law operand")
        surprise_index = next((i for i, op in enumerate(operands) if op.op == "surprise"), None)
        fill_index = next((i for i, op in enumerate(operands) if op.op == "fill"), None)
        if surprise_index is None or fill_index is None or surprise_index == fill_index:
            raise OneError("root Law relation must be Surprise plus Fill")
        source_op = operands[surprise_index]
        fill_op = operands[fill_index]
        source_ref = child.refs[surprise_index]
        fill_ref = child.refs[fill_index]
        if (
            not _full_ref(source_ref, source_op)
            or not _full_ref(fill_ref, fill_op)
            or source_op.refs
            or source_op.length != len(source_op.surprise)
            or fill_op.refs
            or fill_op.count != child.length
            or fill_op.length != child.length
            or source_op.length != child.length
        ):
            raise OneError("root Law relation geometry is not fusible")
        kind = 1 if child.op == "xor" else 2
        specs.append((kind, source_op.surprise, fill_op.value, child.length))
        stored_source_bytes += child.length
        derived_bytes += child.length
        offset += child.length

    if offset != root.length:
        raise OneError("root Law fused command coverage mismatch")

    keepers: list[ctypes.c_char_p] = []
    commands = (_Cmd * len(specs))()
    dst = 0
    for i, (kind, source, value, length) in enumerate(specs):
        keeper = ctypes.c_char_p(source)
        keepers.append(keeper)
        commands[i].src = ctypes.cast(keeper, _U8P)
        commands[i].dst = dst
        commands[i].len = length
        commands[i].value = value
        commands[i].kind = kind
        dst += length

    # Traffic model charges stored-source reads, final writes, and one root-auth read.
    # A relation source may legitimately be read once for its direct COPY and once for a
    # derived child; both appear as separate commands and are therefore both charged.
    source_reads = sum(length for _, _, _, length in specs)
    modeled_traffic = source_reads + root.length + root.length
    return FusedRootLawPlan(
        root.name,
        root.length,
        root.sha256_hex,
        commands,
        tuple(keepers),
        len(specs),
        stored_source_bytes,
        derived_bytes,
        modeled_traffic,
    )


def execute_fused_root_law_plan(plan: FusedRootLawPlan) -> tuple[dict[str, bytes], FusedRootLawStats]:
    sink = bytearray(plan.root_length)
    if plan.root_length:
        view = (ctypes.c_uint8 * plan.root_length).from_buffer(sink)
        ptr = ctypes.cast(view, _U8P)
    else:
        ptr = _U8P()
    rc = _library().one_execute_root_law_plan(ptr, plan.root_length, plan.commands, plan.command_count)
    if rc:
        raise OneError(f"root Law fusion kernel rejected with status {rc}")
    value = bytes(sink)
    if sha256(value).hexdigest() != plan.root_sha256:
        raise OneError("root Law fusion sha256 mismatch")
    return {plan.root_name: value}, FusedRootLawStats(
        plan.root_length,
        plan.command_count,
        plan.stored_source_bytes,
        plan.derived_bytes,
        plan.modeled_traffic_bytes,
    )

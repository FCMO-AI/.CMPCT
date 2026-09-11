"""ONE-G0.2 native mixed terminal replay experiment.

This lowers an already-validated PreparedTerminalPlan into one bounded native COPY/FILL
schedule per root. The stored ONE Program is unchanged. Preparation is explicit and is
measured separately by the falsifier; hot replay still pays root allocation, hashing,
output freezing, and the native call.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from experiments.one.fused_terminal_reader import FusedTerminalStats
from experiments.one.ir import OneError
from experiments.one.prepared_terminal_plan import PreparedTerminalPlan

COPY = 0
FILL = 1

class _MixedCmd(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint64),
        ("length", ctypes.c_uint64),
        ("source_offset", ctypes.c_uint64),
        ("value", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
    ]

@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("native_mixed_terminal_plan_kernel.c")
    build_dir = Path(tempfile.mkdtemp(prefix="cmpct-one-mixed-terminal-"))
    output = build_dir / "libone_mixed_terminal.so"
    subprocess.run(["cc","-O3","-std=c11","-fPIC","-shared",str(source),"-o",str(output)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    lib = ctypes.CDLL(str(output))
    fn = lib.one_apply_mixed_terminal_schedule
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(_MixedCmd),ctypes.c_size_t]
    fn.restype = ctypes.c_int
    return lib

@dataclass
class NativeMixedRoot:
    name: str
    length: int
    sha256_hex: str
    surprise_blob: bytes
    surprise_buffer: object
    commands: object
    command_count: int
    stored_surprise_read_bytes: int
    sink_write_bytes: int

@dataclass
class NativeMixedTerminalPlan:
    roots: tuple[NativeMixedRoot, ...]
    max_work_bytes: int


def compile_native_mixed_terminal_plan(plan: PreparedTerminalPlan) -> NativeMixedTerminalPlan:
    """Lower an already validated generic terminal plan into a packed native schedule."""
    roots=[]
    for root in plan.roots:
        steps=[]
        blob=bytearray()
        for offset,payload,lo,hi in root.surprise_steps:
            width=hi-lo
            src_off=len(blob)
            blob.extend(memoryview(payload)[lo:hi])
            steps.append((int(offset),width,src_off,0,COPY))
        if root.fill_count:
            for i in range(root.fill_count):
                c=root.fill_commands[i]
                steps.append((int(c.offset),int(c.length),0,int(c.value),FILL))
        steps.sort(key=lambda x:x[0])
        cursor=0
        for offset,width,src_off,value,kind in steps:
            if width < 0 or offset != cursor or offset + width > root.length:
                raise OneError("mixed terminal schedule must cover root exactly without gaps/overlap")
            if kind == COPY and src_off + width > len(blob):
                raise OneError("mixed terminal COPY exceeds packed Surprise bytes")
            cursor += width
        if cursor != root.length:
            raise OneError("mixed terminal schedule does not cover complete root")
        cmd_array=(_MixedCmd * len(steps))(*(_MixedCmd(off,width,src,value,kind) for off,width,src,value,kind in steps)) if steps else None
        packed=bytes(blob)
        surprise_buffer=(ctypes.c_uint8 * len(packed)).from_buffer_copy(packed) if packed else None
        roots.append(NativeMixedRoot(root.name,root.length,root.sha256_hex,packed,surprise_buffer,cmd_array,len(steps),root.stored_surprise_read_bytes,root.sink_write_bytes))
    return NativeMixedTerminalPlan(tuple(roots),plan.max_work_bytes)


def _apply_root(root: NativeMixedRoot) -> bytes:
    sink=bytearray(root.length)
    sink_ptr=ctypes.cast((ctypes.c_uint8 * len(sink)).from_buffer(sink),ctypes.POINTER(ctypes.c_uint8)) if sink else ctypes.POINTER(ctypes.c_uint8)()
    source_ptr=ctypes.cast(root.surprise_buffer,ctypes.POINTER(ctypes.c_uint8)) if root.surprise_buffer is not None else ctypes.POINTER(ctypes.c_uint8)()
    rc=_library().one_apply_mixed_terminal_schedule(sink_ptr,len(sink),source_ptr,len(root.surprise_blob),root.commands,root.command_count)
    if rc != 0:
        raise OneError(f"native mixed terminal schedule rejected with status {rc}")
    if sha256(sink).hexdigest() != root.sha256_hex:
        raise OneError(f"root {root.name!r} sha256 mismatch")
    return bytes(sink)


def execute_native_mixed_terminal_plan(plan: NativeMixedTerminalPlan) -> tuple[dict[str,bytes],FusedTerminalStats]:
    outputs={}
    stored_reads=sink_writes=hash_reads=freeze_traffic=peak_temporary=0
    for root in plan.roots:
        outputs[root.name]=_apply_root(root)
        stored_reads += root.stored_surprise_read_bytes
        sink_writes += root.sink_write_bytes
        hash_reads += root.length
        freeze_traffic += 2 * root.length
        peak_temporary=max(peak_temporary,root.length)
    modeled=stored_reads+sink_writes+hash_reads+freeze_traffic
    if modeled > plan.max_work_bytes:
        raise OneError("native mixed terminal modeled memory traffic exceeds declared work limit")
    return outputs,FusedTerminalStats(stored_reads,sink_writes,hash_reads,freeze_traffic,modeled,peak_temporary,len(outputs))

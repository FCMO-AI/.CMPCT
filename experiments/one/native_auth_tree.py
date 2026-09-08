"""Research-only ctypes wrapper for the exact ONE-G0.2 authenticated-range tree grammar."""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
from math import ceil
from pathlib import Path
import subprocess
import tempfile


HASH_BYTES = 32


@dataclass(frozen=True)
class NativeAuthTree:
    total_len: int
    leaf_bytes: int
    level_widths: tuple[int, ...]
    packed_nodes: bytes
    root: bytes

    @property
    def node_count(self) -> int:
        return len(self.packed_nodes) // HASH_BYTES

    @property
    def stored_index_bytes(self) -> int:
        return 4 + HASH_BYTES * (self.node_count - 1)

    def levels(self) -> tuple[tuple[bytes, ...], ...]:
        levels=[]; off=0
        for width in self.level_widths:
            n=width*HASH_BYTES
            chunk=self.packed_nodes[off:off+n]
            levels.append(tuple(chunk[i:i+HASH_BYTES] for i in range(0,n,HASH_BYTES)))
            off += n
        return tuple(levels)


def _widths(total_len: int, leaf_bytes: int) -> tuple[int, ...]:
    width=max(1,ceil(total_len/leaf_bytes)); out=[]
    while True:
        out.append(width)
        if width == 1: return tuple(out)
        width=(width+1)//2


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source=Path(__file__).with_name("native_auth_tree_kernel.c")
    build_dir=Path(tempfile.mkdtemp(prefix="cmpct-one-native-auth-"))
    output=build_dir/"libone_native_auth.so"
    subprocess.run(
        ["cc","-O3","-std=c11","-fPIC","-shared",str(source),"-lcrypto","-o",str(output)],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
    )
    lib=ctypes.CDLL(str(output))
    fn=lib.one_auth_tree_native
    fn.argtypes=[
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    fn.restype=ctypes.c_int
    return lib


def build_auth_tree_native(data: bytes, leaf_bytes: int) -> NativeAuthTree:
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if type(leaf_bytes) is not int or leaf_bytes <= 0 or leaf_bytes > 0xFFFFFFFF:
        raise ValueError("leaf_bytes must be positive uint32")
    widths=_widths(len(data),leaf_bytes)
    node_count=sum(widths)
    out=(ctypes.c_uint8*(node_count*HASH_BYTES))()
    root=(ctypes.c_uint8*HASH_BYTES)()
    actual=ctypes.c_size_t()
    if data:
        source=(ctypes.c_uint8*len(data)).from_buffer_copy(data)
        source_ptr=ctypes.cast(source,ctypes.POINTER(ctypes.c_uint8))
    else:
        source=None
        source_ptr=ctypes.POINTER(ctypes.c_uint8)()
    rc=_library().one_auth_tree_native(
        source_ptr,len(data),leaf_bytes,out,node_count,ctypes.byref(actual),root,
    )
    if rc != 0:
        raise RuntimeError(f"native auth-tree builder failed with status {rc}")
    if actual.value != node_count:
        raise RuntimeError("native auth-tree node-count mismatch")
    return NativeAuthTree(
        total_len=len(data),leaf_bytes=leaf_bytes,level_widths=widths,
        packed_nodes=bytes(out),root=bytes(root),
    )

"""Research-only ctypes wrapper for the exact ONE-G0.2 authenticated-range tree grammar."""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
from math import ceil
from pathlib import Path
import subprocess
import tempfile

from experiments.one.auth_tree import RangeProof


HASH_BYTES = 32


@dataclass(frozen=True)
class NativeAuthTree:
    total_len: int
    leaf_bytes: int
    level_widths: tuple[int, ...]
    level_offsets_nodes: tuple[int, ...]
    packed_nodes: bytes
    root: bytes

    @property
    def leaf_count(self) -> int:
        return self.level_widths[0]

    @property
    def node_count(self) -> int:
        return len(self.packed_nodes) // HASH_BYTES

    @property
    def stored_index_bytes(self) -> int:
        return 4 + HASH_BYTES * (self.node_count - 1)

    def _level_node_offset(self, level: int, index: int) -> int:
        if level < 0 or level >= len(self.level_widths):
            raise IndexError("auth-tree level out of range")
        width=self.level_widths[level]
        if index < 0 or index >= width:
            raise IndexError("auth-tree node out of range")
        return (self.level_offsets_nodes[level] + index) * HASH_BYTES

    def digest_at(self, level: int, index: int) -> bytes:
        """Return one stored digest without materializing any complete level."""
        off=self._level_node_offset(level,index)
        return self.packed_nodes[off:off+HASH_BYTES]

    def levels(self) -> tuple[tuple[bytes, ...], ...]:
        """Reference/debug expansion only; the selective path must not require this."""
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


def _offsets(widths: tuple[int, ...]) -> tuple[int, ...]:
    out=[]; total=0
    for width in widths:
        out.append(total); total += width
    return tuple(out)


def _proof_leaf_interval(data: bytes, tree: NativeAuthTree, start: int, length: int) -> tuple[int,int]:
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if start < 0 or length < 0 or start + length > len(data) or len(data) != tree.total_len:
        raise ValueError("invalid proof range")
    if length == 0:
        first=min(start // tree.leaf_bytes,tree.leaf_count-1)
        return first,first
    return start // tree.leaf_bytes,(start+length-1)//tree.leaf_bytes


def prove_range_packed(data: bytes, tree: NativeAuthTree, start: int, length: int) -> RangeProof:
    """Original set-based packed proof candidate retained as exact negative evidence."""
    first,last=_proof_leaf_interval(data,tree,start,length)
    selected=set(range(first,last+1))
    payloads=tuple(data[i*tree.leaf_bytes:min(len(data),(i+1)*tree.leaf_bytes)] for i in sorted(selected))
    siblings=[]
    current=set(selected)
    for level_no,width in enumerate(tree.level_widths[:-1]):
        needed=set()
        for idx in current:
            sib=idx ^ 1
            if sib < width and sib not in current:
                needed.add(sib)
        for idx in sorted(needed):
            siblings.append((level_no,idx,tree.digest_at(level_no,idx)))
        current={idx//2 for idx in current}
    return RangeProof(tree.total_len,tree.leaf_bytes,first,payloads,tuple(siblings))


def prove_range_packed_interval(data: bytes, tree: NativeAuthTree, start: int, length: int) -> RangeProof:
    """Generate the same RangeProof using contiguous-interval boundary arithmetic.

    Requested leaves are contiguous. At each binary-tree level their ancestors remain a
    contiguous interval, so only the two interval boundaries can require external sibling
    hashes. This removes per-level set construction/scanning while retaining byte-identical
    proof ordering and reading exactly the same packed sibling digests.
    """
    first,last=_proof_leaf_interval(data,tree,start,length)
    payloads=tuple(
        data[i*tree.leaf_bytes:min(len(data),(i+1)*tree.leaf_bytes)]
        for i in range(first,last+1)
    )
    siblings=[]
    lo=first; hi=last
    for level_no,width in enumerate(tree.level_widths[:-1]):
        # sorted(set-based-needed) is exactly left boundary first, then right boundary.
        if lo & 1:
            left=lo-1
            siblings.append((level_no,left,tree.digest_at(level_no,left)))
        right=hi+1
        if not (hi & 1) and right < width:
            siblings.append((level_no,right,tree.digest_at(level_no,right)))
        lo //= 2; hi //= 2
    return RangeProof(tree.total_len,tree.leaf_bytes,first,payloads,tuple(siblings))


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
        total_len=len(data),leaf_bytes=leaf_bytes,level_widths=widths,level_offsets_nodes=_offsets(widths),
        packed_nodes=bytes(out),root=bytes(root),
    )

"""Research-only native verifier for the exact ONE-G0.2 authenticated-range grammar."""
from __future__ import annotations

import ctypes
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

from experiments.one.auth_tree import HASH_BYTES, RangeProof


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source=Path(__file__).with_name("native_auth_verify_kernel.c")
    build_dir=Path(tempfile.mkdtemp(prefix="cmpct-one-native-auth-verify-"))
    output=build_dir/"libone_native_auth_verify.so"
    subprocess.run(
        ["cc","-O3","-std=c11","-fPIC","-shared",str(source),"-lcrypto","-o",str(output)],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
    )
    lib=ctypes.CDLL(str(output))
    fn=lib.one_auth_verify_interval_native
    fn.argtypes=[
        ctypes.c_uint64,ctypes.c_uint32,ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_uint64,ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,
    ]
    fn.restype=ctypes.c_int
    return lib


def verify_range_native(proof: RangeProof, expected_root: bytes, start: int, length: int) -> bytes:
    """Verify an existing RangeProof in one native interval fold.

    The proof grammar and hashes are unchanged. This wrapper intentionally accepts the
    reference RangeProof so the experiment isolates verification implementation rather
    than silently introducing a second reader-visible proof representation.
    """
    if type(expected_root) is not bytes or len(expected_root) != HASH_BYTES:
        raise ValueError("invalid expected root")
    if type(start) is not int or type(length) is not int or start < 0 or length < 0:
        raise ValueError("invalid verification request")
    if type(proof.total_len) is not int or type(proof.leaf_bytes) is not int or proof.leaf_bytes <= 0:
        raise ValueError("invalid proof metadata")
    if start + length > proof.total_len:
        raise ValueError("invalid verification request")

    payload_blob=b"".join(proof.leaf_payloads)
    if payload_blob:
        payload_arr=(ctypes.c_uint8*len(payload_blob)).from_buffer_copy(payload_blob)
        payload_ptr=ctypes.cast(payload_arr,ctypes.POINTER(ctypes.c_uint8))
    else:
        payload_arr=None; payload_ptr=ctypes.POINTER(ctypes.c_uint8)()

    count=len(proof.siblings)
    levels=(ctypes.c_uint32*count)()
    indices=(ctypes.c_uint64*count)()
    hashes=(ctypes.c_uint8*(count*HASH_BYTES))()
    for i,item in enumerate(proof.siblings):
        if type(item) is not tuple or len(item) != 3:
            raise ValueError("malformed proof sibling")
        level,index,digest=item
        if type(level) is not int or type(index) is not int or level < 0 or index < 0 or level > 0xFFFFFFFF or index > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("malformed proof sibling")
        if type(digest) is not bytes or len(digest) != HASH_BYTES:
            raise ValueError("bad proof hash")
        levels[i]=level; indices[i]=index
        for j,b in enumerate(digest): hashes[i*HASH_BYTES+j]=b

    root_arr=(ctypes.c_uint8*HASH_BYTES).from_buffer_copy(expected_root)
    out=(ctypes.c_uint8*max(1,length))()
    rc=_library().one_auth_verify_interval_native(
        proof.total_len,proof.leaf_bytes,proof.first_leaf,
        payload_ptr,len(payload_blob),len(proof.leaf_payloads),
        levels,indices,hashes,count,root_arr,start,length,out,length,
    )
    if rc != 0:
        if rc in (-1,-2,-5):
            raise ValueError("invalid or incomplete range proof")
        if rc == -4:
            raise ValueError("range authentication failed")
        raise RuntimeError(f"native range verification failed with status {rc}")
    return bytes(out[:length])

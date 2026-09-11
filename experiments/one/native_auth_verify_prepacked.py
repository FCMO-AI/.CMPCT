"""Research-only prepacked boundary for the ONE-G0.2 native auth verifier.

This module does not define a new proof grammar. It prepares the existing ``RangeProof``
into the exact ctypes arrays consumed by ``one_auth_verify_interval_native`` so a
falsifier can distinguish native hash/fold cost from repeated Python->ctypes proof
marshalling cost.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass

from experiments.one.auth_tree import HASH_BYTES, RangeProof
from experiments.one.native_auth_verify import _library


@dataclass
class PreparedNativeRangeProof:
    total_len: int
    leaf_bytes: int
    first_leaf: int
    payload_count: int
    payload_blob: bytes
    payload_arr: object | None
    payload_ptr: object
    sibling_count: int
    levels: object
    indices: object
    hashes: object
    root_arr: object


def prepare_native_range_proof(proof: RangeProof, expected_root: bytes) -> PreparedNativeRangeProof:
    """Marshal one existing proof into stable native buffers outside the hot verify call."""
    if type(expected_root) is not bytes or len(expected_root) != HASH_BYTES:
        raise ValueError("invalid expected root")
    if type(proof.total_len) is not int or type(proof.leaf_bytes) is not int or proof.leaf_bytes <= 0:
        raise ValueError("invalid proof metadata")
    if type(proof.first_leaf) is not int or proof.first_leaf < 0:
        raise ValueError("invalid proof metadata")

    payload_blob=b"".join(proof.leaf_payloads)
    if payload_blob:
        payload_arr=(ctypes.c_uint8*len(payload_blob)).from_buffer_copy(payload_blob)
        payload_ptr=ctypes.cast(payload_arr,ctypes.POINTER(ctypes.c_uint8))
    else:
        payload_arr=None
        payload_ptr=ctypes.POINTER(ctypes.c_uint8)()

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
        levels[i]=level
        indices[i]=index
        for j,b in enumerate(digest):
            hashes[i*HASH_BYTES+j]=b

    root_arr=(ctypes.c_uint8*HASH_BYTES).from_buffer_copy(expected_root)
    return PreparedNativeRangeProof(
        total_len=proof.total_len,
        leaf_bytes=proof.leaf_bytes,
        first_leaf=proof.first_leaf,
        payload_count=len(proof.leaf_payloads),
        payload_blob=payload_blob,
        payload_arr=payload_arr,
        payload_ptr=payload_ptr,
        sibling_count=count,
        levels=levels,
        indices=indices,
        hashes=hashes,
        root_arr=root_arr,
    )


def verify_range_native_prepacked(prepared: PreparedNativeRangeProof, start: int, length: int) -> bytes:
    """Run only the existing native interval verifier plus output allocation/conversion.

    Proof bytes, coordinates, payload bytes and expected root are unchanged from the
    existing RangeProof. The only removed work is repeated Python-to-ctypes marshalling.
    """
    if type(start) is not int or type(length) is not int or start < 0 or length < 0:
        raise ValueError("invalid verification request")
    if start + length > prepared.total_len:
        raise ValueError("invalid verification request")

    out=(ctypes.c_uint8*max(1,length))()
    rc=_library().one_auth_verify_interval_native(
        prepared.total_len,
        prepared.leaf_bytes,
        prepared.first_leaf,
        prepared.payload_ptr,
        len(prepared.payload_blob),
        prepared.payload_count,
        prepared.levels,
        prepared.indices,
        prepared.hashes,
        prepared.sibling_count,
        prepared.root_arr,
        start,
        length,
        out,
        length,
    )
    if rc != 0:
        if rc in (-1,-2,-5):
            raise ValueError("invalid or incomplete range proof")
        if rc == -4:
            raise ValueError("range authentication failed")
        raise RuntimeError(f"native range verification failed with status {rc}")
    return bytes(out[:length])

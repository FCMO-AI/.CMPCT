from __future__ import annotations

"""Research-only exact Analytics inverse-root framing oracle.

This instrument asks whether the exact loose-NPY <-> NPZ-member inverse relation that
historical CMPNX5 already exploits has enough complete-byte headroom to justify pricing
inside canonical r25 framing. It does not mutate the shipping builder/reader.

The measured candidate deliberately uses 512-KiB independently compressed Zstd-19
roots and reconstructs the NPZ features member by exact deterministic raw-DEFLATE
recompression from the authenticated loose features.npy bytes. The exact source tree
must match the frozen Analytics workload.
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import zipfile
import zlib

CHUNK = 512 * 1024
LEVEL = 19
PHYSICAL_HEADER_CHARGE = 64
INVERSE_META_CHARGE = 352
EXPECTED_TREE = "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d"
V029_FLOOR = 6_135_325
EXTERNAL_ZSTD19 = 9_337_546

_zstd = ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so")
_zstd.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
_zstd.ZSTD_compressBound.restype = ctypes.c_size_t
_zstd.ZSTD_compress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int
]
_zstd.ZSTD_compress.restype = ctypes.c_size_t
_zstd.ZSTD_isError.argtypes = [ctypes.c_size_t]
_zstd.ZSTD_isError.restype = ctypes.c_uint


def _treehash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = p.relative_to(root).as_posix().encode()
        raw = p.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
    return h.hexdigest()


def _zstd_size(raw: bytes) -> int:
    src = ctypes.create_string_buffer(raw)
    cap = int(_zstd.ZSTD_compressBound(len(raw)))
    dst = ctypes.create_string_buffer(cap)
    n = int(_zstd.ZSTD_compress(dst, cap, src, len(raw), LEVEL))
    if _zstd.ZSTD_isError(n):
        raise RuntimeError("Zstd compression failed")
    return n


def run(root: Path) -> dict:
    live_tree = _treehash(root)
    if live_tree != EXPECTED_TREE:
        raise RuntimeError(f"Analytics source drift: {live_tree} != {EXPECTED_TREE}")

    npz = root / "features_compressed.npz"
    loose = root / "features.npy"
    npz_raw = npz.read_bytes()
    loose_raw = loose.read_bytes()

    member_rows = []
    payload_total = 0
    feature = None
    labels = None
    with zipfile.ZipFile(npz) as ar:
        for zi in ar.infolist():
            if zi.is_dir():
                continue
            hdr = struct.unpack_from("<IHHHHHIIIHH", npz_raw, zi.header_offset)
            name_len, extra_len = hdr[-2], hdr[-1]
            payload_off = zi.header_offset + 30 + name_len + extra_len
            payload = npz_raw[payload_off : payload_off + zi.compress_size]
            plain = ar.read(zi)
            payload_total += len(payload)
            levels = []
            for level in range(10):
                co = zlib.compressobj(level, zlib.DEFLATED, -15)
                if co.compress(plain) + co.flush() == payload:
                    levels.append(level)
            row = {
                "name": zi.filename,
                "compressed_bytes": len(payload),
                "logical_bytes": len(plain),
                "exact_zlib_levels": levels,
                "matches_loose_features": plain == loose_raw,
            }
            member_rows.append(row)
            item = (zi, payload_off, payload, plain, levels)
            if plain == loose_raw:
                feature = item
            if zi.filename == "labels.npy":
                labels = item

    if feature is None or labels is None or 6 not in feature[4]:
        raise RuntimeError("Expected exact Analytics inverse relation was not reproduced")

    fzi, foff, fpayload, fplain, _ = feature
    lzi, loff, lpayload, lplain, _ = labels
    co = zlib.compressobj(6, zlib.DEFLATED, -15)
    regenerated = co.compress(loose_raw) + co.flush()
    if regenerated != fpayload:
        raise RuntimeError("features.npy did not reproduce exact NPZ Deflate payload")

    # Prove byte-identical NPZ reconstruction by replacing only the features stream
    # with the deterministic recompression of the separately authenticated loose file.
    rebuilt = bytearray()
    cursor = 0
    for zi, off, payload, plain, levels in sorted((feature, labels), key=lambda x: x[1]):
        rebuilt += npz_raw[cursor:off]
        rebuilt += regenerated if zi.filename == "features.npy" else payload
        cursor = off + len(payload)
    rebuilt += npz_raw[cursor:]
    if bytes(rebuilt) != npz_raw:
        raise RuntimeError("NPZ exact reconstruction failed")

    skeleton_bytes = len(npz_raw) - payload_total
    total = skeleton_bytes + len(lpayload) + INVERSE_META_CHARGE
    rows = []
    started = time.perf_counter()
    for p in sorted(root.iterdir()):
        if not p.is_file() or p.name == npz.name:
            continue
        raw = p.read_bytes()
        payload = sum(_zstd_size(raw[i : i + CHUNK]) for i in range(0, len(raw), CHUNK))
        chunks = math.ceil(len(raw) / CHUNK)
        charged = payload + PHYSICAL_HEADER_CHARGE * chunks
        total += charged
        rows.append({
            "file": p.name,
            "logical_bytes": len(raw),
            "chunks": chunks,
            "zstd19_payload_bytes": payload,
            "charged_bytes": charged,
        })

    return {
        "schema": "cmpct-v030-analytics-inverse-root-oracle-v1",
        "source_tree_sha256": live_tree,
        "exact_npz_reconstruction": True,
        "member_rows": member_rows,
        "npz_bytes": len(npz_raw),
        "npz_skeleton_bytes": skeleton_bytes,
        "retained_labels_stream_bytes": len(lpayload),
        "physical_chunk_bytes": CHUNK,
        "zstd_level": LEVEL,
        "physical_header_charge_bytes": PHYSICAL_HEADER_CHARGE,
        "inverse_metadata_charge_bytes": INVERSE_META_CHARGE,
        "rows": rows,
        "charged_complete_bytes": total,
        "inherited_v029_floor_bytes": V029_FLOOR,
        "margin_vs_v029_floor_bytes": V029_FLOOR - total,
        "external_zstd19_bytes": EXTERNAL_ZSTD19,
        "margin_vs_external_zstd19_bytes": EXTERNAL_ZSTD19 - total,
        "oracle_wall_s": time.perf_counter() - started,
        "claim_boundary": (
            "research-only exact information/framing headroom; no product, locality, "
            "recovery, portability, promotion, or release credit"
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

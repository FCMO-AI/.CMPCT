from __future__ import annotations

"""Physical-locality falsifier for a bounded dual-view Analytics owner.

The exact NPZ owner is a strong density result but its internal raw-DEFLATE member cannot satisfy the
inherited 8x cold selective-read reconstruction law with legal independent-history restart points. This
experiment changes the research representation boundary instead of weakening that law: retain the exact
NPZ bytes as the canonical physical owner for NPZ byte ranges, and add an independently compressed NPY
read view solely for selective access to the external NPY.

The NPY chunk size is fixed before measurement at 16 KiB. A 4 KiB request can intersect at most two
chunks, so worst-case decoded work is at most 32 KiB = 8x. There is no chunk-size sweep. The exact NPZ is
range-authenticated with fixed 8 KiB Merkle leaves so an arbitrary 4 KiB range touches at most two data
leaves. The NPY chunk index is fixed-width and Merkle-authenticated; cold reads pread only the required
records, proofs and compressed frames. All duplicate-view bytes, index/tree bytes and the range root are
charged to candidate stored size.

Advance requires all of the following on the frozen Analytics workload: byte-exact semantic tree,
candidate below the accepted source-sealed v0.29 Analytics floor, <=8x physical amplification for every
probed NPZ/NPY 4 KiB boundary read, <=8x NPY reconstruction amplification, and touched-data corruption
rejection. This is diagnostic research packaging only; no product format or selector changes.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import struct
import time

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-analytics-dual-view-chunked-locality-v1"
REQUEST = 4 * 1024
NPY_CHUNK = 4 * REQUEST          # arbitrary 4 KiB request can cross <=2 chunks => <=8x decode
NPZ_LEAF = 2 * REQUEST           # arbitrary 4 KiB request can cross <=2 leaves => <=4x data I/O
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
MAGIC = b"R4DV1\0\0\0"
RECORD = struct.Struct("<QII32s")  # pack offset, compressed bytes, raw bytes, compressed-frame hash
ROOT = struct.Struct("<8sQII32sQII32s32s")
# magic, npz(size, leaves, leaf_size, root), npy(size, chunks, chunk_size, index_root), full_npy_sha


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _merkle_from_hashes(leaves: list[bytes]) -> tuple[list[list[bytes]], bytes]:
    if not leaves:
        leaves = [_h(b"")]
    levels = [leaves]
    while len(levels[-1]) > 1:
        prev = levels[-1]
        levels.append([
            _h(prev[i] + (prev[i + 1] if i + 1 < len(prev) else prev[i]))
            for i in range(0, len(prev), 2)
        ])
    tree = b"".join(node for level in levels[:-1] for node in level)
    return levels, tree


def _merkle_data(raw: bytes, leaf_size: int) -> tuple[list[list[bytes]], bytes]:
    leaves = [_h(raw[i:i + leaf_size]) for i in range(0, len(raw), leaf_size)] or [_h(b"")]
    return _merkle_from_hashes(leaves)


def _counts(n: int) -> list[int]:
    out = [n]
    while out[-1] > 1:
        out.append((out[-1] + 1) // 2)
    return out


def _offsets(n: int) -> list[int]:
    out = []
    pos = 0
    for count in _counts(n)[:-1]:
        out.append(pos)
        pos += count * 32
    return out


def _verify_leaf(tree_fd: int, leaves: int, root: bytes, idx: int, leaf_hash: bytes) -> tuple[bool, int]:
    node = leaf_hash
    proof_bytes = 0
    offsets = _offsets(leaves)
    for level, count in enumerate(_counts(leaves)[:-1]):
        sibling = idx ^ 1
        if sibling >= count:
            sib = node
        else:
            sib = os.pread(tree_fd, 32, offsets[level] + sibling * 32)
            proof_bytes += len(sib)
            if len(sib) != 32:
                raise ValueError("truncated Merkle proof")
        node = _h(node + sib) if idx % 2 == 0 else _h(sib + node)
        idx //= 2
    return node == root, proof_bytes


def _build_view(bundle: Path, npy_raw: bytes) -> dict:
    npz_raw = (bundle / "owner.npz").read_bytes()
    npz_levels, npz_tree = _merkle_data(npz_raw, NPZ_LEAF)
    (bundle / "owner.npz.tree").write_bytes(npz_tree)

    cctx = zstd.ZstdCompressor(level=3, write_checksum=True, write_content_size=True)
    pack = bytearray()
    records: list[bytes] = []
    t0 = time.perf_counter()
    cpu0 = time.process_time()
    for start in range(0, len(npy_raw), NPY_CHUNK):
        raw = npy_raw[start:start + NPY_CHUNK]
        frame = cctx.compress(raw)
        off = len(pack)
        pack.extend(frame)
        records.append(RECORD.pack(off, len(frame), len(raw), _h(frame)))
    encode_wall = time.perf_counter() - t0
    encode_cpu = time.process_time() - cpu0
    (bundle / "npy.view").write_bytes(pack)
    index = b"".join(records)
    (bundle / "npy.view.index").write_bytes(index)
    idx_levels, idx_tree = _merkle_from_hashes([_h(r) for r in records])
    (bundle / "npy.view.index.tree").write_bytes(idx_tree)

    root = ROOT.pack(
        MAGIC,
        len(npz_raw), len(npz_levels[0]), NPZ_LEAF, npz_levels[-1][0],
        len(npy_raw), len(records), NPY_CHUNK, idx_levels[-1][0], _h(npy_raw),
    )
    (bundle / "range.root").write_bytes(root)
    added = sum((bundle / name).stat().st_size for name in (
        "owner.npz.tree", "npy.view", "npy.view.index", "npy.view.index.tree", "range.root"
    ))
    return {
        "added_view_bytes": added,
        "npz_tree_bytes": len(npz_tree),
        "npy_view_bytes": len(pack),
        "npy_index_bytes": len(index),
        "npy_index_tree_bytes": len(idx_tree),
        "range_root_bytes": len(root),
        "npz_leaves": len(npz_levels[0]),
        "npy_chunks": len(records),
        "view_encode_wall_s": encode_wall,
        "view_encode_cpu_s": encode_cpu,
    }


def _read_root(bundle: Path):
    raw = (bundle / "range.root").read_bytes()
    if len(raw) != ROOT.size:
        raise ValueError("bad range root size")
    vals = ROOT.unpack(raw)
    if vals[0] != MAGIC:
        raise ValueError("bad range root magic")
    return raw, vals


def _cold_npz(bundle: Path, start: int, length: int) -> tuple[bytes, dict]:
    root_raw, vals = _read_root(bundle)
    _, size, leaves, leaf_size, root, _, _, _, _, _ = vals
    if start < 0 or length < 0 or start + length > size:
        raise ValueError("bad NPZ range")
    out = bytearray()
    touched: dict[int, bytes] = {}
    proof = 0
    with open(bundle / "owner.npz", "rb", buffering=0) as df, open(bundle / "owner.npz.tree", "rb", buffering=0) as tf:
        pos = start
        remaining = length
        while remaining:
            idx = pos // leaf_size
            leaf_off = idx * leaf_size
            if idx not in touched:
                raw = os.pread(df.fileno(), min(leaf_size, size - leaf_off), leaf_off)
                ok, pb = _verify_leaf(tf.fileno(), leaves, root, idx, _h(raw))
                if not ok:
                    raise ValueError("NPZ range authentication failed")
                touched[idx] = raw
                proof += pb
            raw = touched[idx]
            inside = pos - leaf_off
            take = min(remaining, len(raw) - inside)
            out.extend(raw[inside:inside + take])
            pos += take
            remaining -= take
    data_bytes = sum(len(x) for x in touched.values())
    physical = len(root_raw) + data_bytes + proof
    return bytes(out), {
        "requested_bytes": length,
        "data_bytes_touched": data_bytes,
        "proof_bytes": proof,
        "root_bytes": len(root_raw),
        "physical_bytes_touched": physical,
        "physical_amplification": physical / max(1, length),
        "reconstruction_bytes": length,
        "reconstruction_amplification": 1.0,
        "leaves_touched": len(touched),
    }


def _record_at(index_fd: int, tree_fd: int, chunks: int, index_root: bytes, idx: int) -> tuple[bytes, int]:
    rec = os.pread(index_fd, RECORD.size, idx * RECORD.size)
    if len(rec) != RECORD.size:
        raise ValueError("truncated NPY view index")
    ok, proof = _verify_leaf(tree_fd, chunks, index_root, idx, _h(rec))
    if not ok:
        raise ValueError("NPY index authentication failed")
    return rec, proof


def _cold_npy(bundle: Path, start: int, length: int) -> tuple[bytes, dict]:
    root_raw, vals = _read_root(bundle)
    _, _, _, _, _, size, chunks, chunk_size, index_root, _ = vals
    if start < 0 or length < 0 or start + length > size:
        raise ValueError("bad NPY range")
    first = start // chunk_size
    last = (start + max(0, length - 1)) // chunk_size if length else first
    decoded: dict[int, bytes] = {}
    frame_bytes = 0
    record_bytes = 0
    proof_bytes = 0
    dctx = zstd.ZstdDecompressor()
    with open(bundle / "npy.view", "rb", buffering=0) as pf, open(bundle / "npy.view.index", "rb", buffering=0) as ix, open(bundle / "npy.view.index.tree", "rb", buffering=0) as tf:
        for idx in range(first, last + 1):
            rec, pb = _record_at(ix.fileno(), tf.fileno(), chunks, index_root, idx)
            proof_bytes += pb
            record_bytes += len(rec)
            off, clen, rlen, frame_hash = RECORD.unpack(rec)
            frame = os.pread(pf.fileno(), clen, off)
            frame_bytes += len(frame)
            if len(frame) != clen or _h(frame) != frame_hash:
                raise ValueError("NPY chunk authentication failed")
            raw = dctx.decompress(frame, max_output_size=rlen)
            if len(raw) != rlen:
                raise ValueError("NPY chunk length mismatch")
            decoded[idx] = raw
    out = bytearray()
    pos = start
    remaining = length
    while remaining:
        idx = pos // chunk_size
        raw = decoded[idx]
        inside = pos - idx * chunk_size
        take = min(remaining, len(raw) - inside)
        out.extend(raw[inside:inside + take])
        pos += take
        remaining -= take
    reconstructed = sum(len(x) for x in decoded.values())
    physical = len(root_raw) + frame_bytes + record_bytes + proof_bytes
    return bytes(out), {
        "requested_bytes": length,
        "frame_bytes_touched": frame_bytes,
        "record_bytes_touched": record_bytes,
        "proof_bytes": proof_bytes,
        "root_bytes": len(root_raw),
        "physical_bytes_touched": physical,
        "physical_amplification": physical / max(1, length),
        "reconstruction_bytes": reconstructed,
        "reconstruction_amplification": reconstructed / max(1, length),
        "chunks_touched": len(decoded),
    }


def _probe_positions(size: int, unit: int) -> list[int]:
    if size <= REQUEST:
        return [0]
    pts = {0, max(0, size // 2 - REQUEST // 2), size - REQUEST}
    # Attack both sides of every physical boundary. These are the worst places for two-unit reads.
    for b in range(unit, size, unit):
        pts.add(max(0, min(size - REQUEST, b - REQUEST // 2)))
        pts.add(max(0, min(size - REQUEST, b - 1)))
    return sorted(pts)


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_dual_view_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_dual_view_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    expected = PRODUCT.treehash(source)

    baseline = work / "baseline.cmpct"
    PRODUCT.build(source, baseline)

    bundle = work / "candidate"
    dual = DUAL._build_candidate(source, bundle, work / "candidate-work")
    preverify = DUAL._extract_candidate(bundle, work / "extract-before-view")
    if preverify["tree_sha256"] != expected:
        raise RuntimeError("dual-owner semantic tree mismatch before read-view addition")
    rel = DUAL._npz_relation(source)["accepted"]
    npy_raw = (source / rel["npy_path"]).read_bytes()
    npz_raw = (source / rel["npz_path"]).read_bytes()

    view = _build_view(bundle, npy_raw)
    candidate_bytes = sum(p.stat().st_size for p in bundle.iterdir() if p.is_file())
    postverify = DUAL._extract_candidate(bundle, work / "extract-after-view")
    if postverify["tree_sha256"] != expected:
        raise RuntimeError("dual-view semantic tree mismatch")

    npz_reads = []
    for start in _probe_positions(len(npz_raw), NPZ_LEAF):
        n = min(REQUEST, len(npz_raw) - start)
        got, stats = _cold_npz(bundle, start, n)
        if got != npz_raw[start:start + n]:
            raise RuntimeError("NPZ cold range mismatch")
        npz_reads.append({"start": start, **stats})

    npy_reads = []
    for start in _probe_positions(len(npy_raw), NPY_CHUNK):
        n = min(REQUEST, len(npy_raw) - start)
        got, stats = _cold_npy(bundle, start, n)
        if got != npy_raw[start:start + n]:
            raise RuntimeError("NPY cold range mismatch")
        npy_reads.append({"start": start, **stats})

    # Corrupt one actually touched NPZ byte and one actually touched NPY compressed frame byte.
    npz_corruption_rejected = False
    probe_start = npz_reads[len(npz_reads) // 2]["start"]
    with open(bundle / "owner.npz", "r+b") as f:
        f.seek(probe_start); old = f.read(1); f.seek(probe_start); f.write(bytes([old[0] ^ 1])); f.flush(); os.fsync(f.fileno())
    try:
        _cold_npz(bundle, probe_start, min(REQUEST, len(npz_raw) - probe_start))
    except ValueError:
        npz_corruption_rejected = True
    finally:
        with open(bundle / "owner.npz", "r+b") as f:
            f.seek(probe_start); f.write(old)

    root_raw, vals = _read_root(bundle)
    chunks = vals[6]; index_root = vals[8]
    with open(bundle / "npy.view.index", "rb", buffering=0) as ix, open(bundle / "npy.view.index.tree", "rb", buffering=0) as tf:
        rec, _ = _record_at(ix.fileno(), tf.fileno(), chunks, index_root, 0)
    off, clen, _, _ = RECORD.unpack(rec)
    npy_corruption_rejected = False
    with open(bundle / "npy.view", "r+b") as f:
        f.seek(off); old2 = f.read(1); f.seek(off); f.write(bytes([old2[0] ^ 1])); f.flush(); os.fsync(f.fileno())
    try:
        _cold_npy(bundle, 0, min(REQUEST, len(npy_raw)))
    except ValueError:
        npy_corruption_rejected = True
    finally:
        with open(bundle / "npy.view", "r+b") as f:
            f.seek(off); f.write(old2)

    max_npz_phys = max(x["physical_amplification"] for x in npz_reads)
    max_npy_phys = max(x["physical_amplification"] for x in npy_reads)
    max_npy_recon = max(x["reconstruction_amplification"] for x in npy_reads)
    supported = (
        candidate_bytes < ACCEPTED_V029_ANALYTICS
        and max_npz_phys <= 8.0
        and max_npy_phys <= 8.0
        and max_npy_recon <= 8.0
        and npz_corruption_rejected
        and npy_corruption_rejected
    )
    rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "tree_sha256": expected,
        "baseline_v030_bytes": baseline.stat().st_size,
        "dual_owner_bytes_before_view": dual["stored_bytes"],
        "candidate_bytes": candidate_bytes,
        "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
        "saving_vs_v030_bytes": baseline.stat().st_size - candidate_bytes,
        "margin_vs_v029_bytes": ACCEPTED_V029_ANALYTICS - candidate_bytes,
        "view": view,
        "max_npz_physical_amplification": max_npz_phys,
        "max_npy_physical_amplification": max_npy_phys,
        "max_npy_reconstruction_amplification": max_npy_recon,
        "npz_probe_count": len(npz_reads),
        "npy_probe_count": len(npy_reads),
        "npz_corruption_rejected": npz_corruption_rejected,
        "npy_corruption_rejected": npy_corruption_rejected,
        "process_peak_rss_kib": rss_kib,
        "npz_selective_reads": npz_reads,
        "npy_selective_reads": npy_reads,
        "hypothesis": {
            "exact_semantic_tree": postverify["tree_sha256"] == expected,
            "candidate_below_v029": candidate_bytes < ACCEPTED_V029_ANALYTICS,
            "all_npz_physical_le_8x": max_npz_phys <= 8.0,
            "all_npy_physical_le_8x": max_npy_phys <= 8.0,
            "all_npy_reconstruction_le_8x": max_npy_recon <= 8.0,
            "touched_corruption_rejected": npz_corruption_rejected and npy_corruption_rejected,
            "supported_for_next_hardening": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "no_chunk_size_sweep": True,
            "npy_chunk_size_derived_from_two_chunk_8x_law": True,
            "npz_leaf_size_derived_from_two_leaf_4k_range": True,
            "actual_file_backed_pread": True,
            "all_duplicate_view_index_tree_root_bytes_charged": True,
            "all_physical_boundaries_adversarially_probed": True,
            "existing_dual_owner_auth_retained_conservatively": True,
        },
        "next_if_supported": "challenge held-out exact container/member relations and product-shaped recovery/native reader complexity before composing with Office",
        "next_if_falsified": "preserve negative; do not sweep chunk size. Attribute failure to duplicated-view storage, physical proof traffic, or compression-frame overhead before another representation change",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-dual-view-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-dual-view.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    keys = (
        "baseline_v030_bytes", "dual_owner_bytes_before_view", "candidate_bytes", "accepted_v029_bytes",
        "saving_vs_v030_bytes", "margin_vs_v029_bytes", "max_npz_physical_amplification",
        "max_npy_physical_amplification", "max_npy_reconstruction_amplification", "npz_probe_count",
        "npy_probe_count", "npz_corruption_rejected", "npy_corruption_rejected", "process_peak_rss_kib",
        "hypothesis",
    )
    print(json.dumps({k: d[k] for k in keys} | {"view": d["view"]}, indent=2))


if __name__ == "__main__":
    main()

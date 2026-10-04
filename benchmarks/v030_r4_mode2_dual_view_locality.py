from __future__ import annotations

"""Falsifier for rehabilitating Analytics Mode2 locality with one bounded exact view.

The composed R4 receipt established that Analytics Mode2 is a large density/creation win but retained
its known selective-read debt: reconstructing the exact NPZ Deflate stream can require work from the
start of the member. Conventional restart-window budgeting already exceeded the available density
margin.

This experiment tests the cheapest representation-boundary counter-invention before inventing a new
codec: keep the external NPY in the ordinary v0.30 product representation, but retain the exact NPZ
bytes as a second *physical view*. The NPZ view is fixed-size segmented and Merkle-authenticated, so a
cold 4 KiB range can verify only the touched data segments plus logarithmic proof nodes. The exact NPZ
view also removes dependence on reproducing a particular zlib Deflate stream at read time.

This is a research bundle only. It changes no shipping format, selector or numeric version. The
hypothesis is intentionally strict: the fully charged dual-view bundle must remain below the accepted
v0.29 Analytics floor *and* the measured cold authenticated NPZ range amplification must stay <=8x.
If either fails, preserve the negative and move to a smaller restart-state/chunk-ownership design.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import struct
import tempfile
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_npz_mode2_owner_inversion as MODE2
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-mode2-dual-view-locality-v1"
BUNDLE_SCHEMA = "cmpct-v030-r4-mode2-dual-view-bundle-v1"
ACCEPTED_V029_ANALYTICS = 6_135_172
GROUP_ROWS = I.GROUP_ROWS
SEGMENT_BYTES = 8 * 1024
RANGE_BYTES = 4 * 1024
MAGIC = b"R4DV1\0\0\0"
META = struct.Struct("<8sQII32s")  # magic, logical bytes, segment bytes, leaves, root


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _sha_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cpu() -> tuple[float, float]:
    me = resource.getrusage(resource.RUSAGE_SELF)
    ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime + me.ru_stime), float(ch.ru_utime + ch.ru_stime)


def _cpu_delta(after: tuple[float, float], before: tuple[float, float]) -> dict:
    self_cpu = after[0] - before[0]
    children_cpu = after[1] - before[1]
    return {"self_cpu_s": self_cpu, "children_cpu_s": children_cpu, "tree_cpu_s": self_cpu + children_cpu}


def _merkle(raw: bytes) -> tuple[list[list[bytes]], bytes, bytes]:
    leaves = [_sha(raw[i:i + SEGMENT_BYTES]) for i in range(0, len(raw), SEGMENT_BYTES)] or [_sha(b"")]
    levels = [leaves]
    while len(levels[-1]) > 1:
        prev = levels[-1]
        nxt = []
        for i in range(0, len(prev), 2):
            left = prev[i]
            right = prev[i + 1] if i + 1 < len(prev) else left
            nxt.append(_sha(left + right))
        levels.append(nxt)
    root = levels[-1][0]
    meta = META.pack(MAGIC, len(raw), SEGMENT_BYTES, len(leaves), root)
    # The root is trusted through meta/auth and is not duplicated in the proof store.
    tree = b"".join(node for level in levels[:-1] for node in level)
    return levels, meta, tree


def _level_counts(leaves: int) -> list[int]:
    out = [leaves]
    while out[-1] > 1:
        out.append((out[-1] + 1) // 2)
    return out


def _level_offsets(leaves: int) -> list[int]:
    counts = _level_counts(leaves)
    out = []
    p = 0
    for n in counts[:-1]:
        out.append(p)
        p += n * 32
    return out


def _verify_segment_with_file(tree_fd: int, meta: bytes, segment_index: int, segment: bytes) -> tuple[bool, int]:
    magic, logical, seg_bytes, leaves, want_root = META.unpack(meta)
    if magic != MAGIC or seg_bytes != SEGMENT_BYTES or not (0 <= segment_index < leaves):
        raise ValueError("invalid dual-view Merkle metadata")
    counts = _level_counts(leaves)
    offsets = _level_offsets(leaves)
    node = _sha(segment)
    idx = segment_index
    proof_bytes = 0
    for level, count in enumerate(counts[:-1]):
        sibling = idx ^ 1
        if sibling >= count:
            sibling_hash = node
        else:
            sibling_hash = os.pread(tree_fd, 32, offsets[level] + sibling * 32)
            proof_bytes += len(sibling_hash)
            if len(sibling_hash) != 32:
                raise ValueError("truncated Merkle proof")
        node = _sha(node + sibling_hash) if idx % 2 == 0 else _sha(sibling_hash + node)
        idx //= 2
    return node == want_root, proof_bytes


def _cold_authenticated_range(bundle: Path, start: int, length: int) -> tuple[bytes, dict]:
    raw_path = bundle / "owner.npz"
    meta = (bundle / "npz.meta").read_bytes()
    auth = (bundle / "auth.bin").read_bytes()
    magic, logical, seg_bytes, leaves, root = META.unpack(meta)
    if magic != MAGIC or start < 0 or length < 0 or start + length > logical:
        raise ValueError("invalid NPZ range")

    # Authenticate the compact NPZ-view root without reading unrelated NPZ data. The global research
    # wrapper auth is deliberately small and the manifest is charged as cold-open metadata.
    manifest = (bundle / "manifest.json").read_bytes()
    expected_prefix = MAGIC + _sha(manifest) + _sha((bundle / "base.cmpct").read_bytes()) + _sha((bundle / "npy.cmpct").read_bytes()) + _sha((bundle / "owner.tcol").read_bytes()) + _sha(meta)
    if auth != expected_prefix:
        raise ValueError("dual-view bundle authentication failed")

    first = start // seg_bytes
    last = (start + max(0, length - 1)) // seg_bytes if length else first
    out = bytearray()
    touched_data = 0
    proof_bytes = 0
    with open(raw_path, "rb", buffering=0) as rf, open(bundle / "npz.tree", "rb", buffering=0) as tf:
        tree_fd = tf.fileno()
        for idx in range(first, last + 1):
            off = idx * seg_bytes
            seg = os.pread(rf.fileno(), min(seg_bytes, logical - off), off)
            ok, pb = _verify_segment_with_file(tree_fd, meta, idx, seg)
            if not ok:
                raise ValueError("NPZ segment authentication failed")
            touched_data += len(seg)
            proof_bytes += pb
            a = max(start, off) - off
            b = min(start + length, off + len(seg)) - off
            if b > a:
                out.extend(seg[a:b])
    metadata_bytes = len(meta) + len(auth) + len(manifest)
    touched = touched_data + proof_bytes + metadata_bytes
    return bytes(out), {
        "requested_bytes": length,
        "data_segment_bytes": touched_data,
        "proof_bytes": proof_bytes,
        "cold_metadata_bytes": metadata_bytes,
        "physical_bytes_touched": touched,
        "amplification": touched / max(1, length),
        "segments_touched": last - first + 1,
    }


def _write_bundle(out: Path, base: Path, npy_archive: Path, tcol: bytes, npz_raw: bytes, manifest: dict) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(base, out / "base.cmpct")
    shutil.copy2(npy_archive, out / "npy.cmpct")
    (out / "owner.tcol").write_bytes(tcol)
    (out / "owner.npz").write_bytes(npz_raw)
    levels, meta, tree = _merkle(npz_raw)
    (out / "npz.meta").write_bytes(meta)
    (out / "npz.tree").write_bytes(tree)
    mraw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    (out / "manifest.json").write_bytes(mraw)
    auth = MAGIC + _sha(mraw) + _sha((out / "base.cmpct").read_bytes()) + _sha((out / "npy.cmpct").read_bytes()) + _sha(tcol) + _sha(meta)
    (out / "auth.bin").write_bytes(auth)
    sizes = {p.name: p.stat().st_size for p in out.iterdir() if p.is_file()}
    return {
        "stored_bytes": sum(sizes.values()),
        "component_bytes": sizes,
        "npz_merkle_levels": len(levels),
        "npz_segments": len(levels[0]),
        "npz_segment_bytes": SEGMENT_BYTES,
        "npz_merkle_root": levels[-1][0].hex(),
    }


def _build_candidate(source: Path, out: Path, work: Path) -> dict:
    tabd = I._discover(source)
    if len(tabd["accepted"]) != 1:
        raise RuntimeError("expected exactly one tabular relation")
    tab = tabd["accepted"][0]
    npzd = DUAL._npz_relation(source)
    rel = npzd["accepted"]
    csvp = source / tab["csv_path"]
    jsonp = source / tab["jsonl_path"]
    npyp = source / rel["npy_path"]
    npzp = source / rel["npz_path"]

    fields, csv_rows = OWNER._parse_csv(csvp.read_bytes())
    jfields, json_rows = OWNER._parse_jsonl(jsonp.read_bytes())
    if fields != jfields or not OWNER._semantic_equal(fields, csv_rows, json_rows):
        raise RuntimeError("tabular relation failed")
    tcol, _ = FAST._encode(
        fields,
        json_rows,
        GROUP_ROWS,
        FAST._line_lengths(csvp.read_bytes(), len(json_rows), GROUP_ROWS, header=True),
        FAST._line_lengths(jsonp.read_bytes(), len(json_rows), GROUP_ROWS, header=False),
    )
    if I._owner_raw(tcol) != (csvp.read_bytes(), jsonp.read_bytes()):
        raise RuntimeError("tabular reconstruction mismatch")

    with tempfile.TemporaryDirectory(prefix="r4-dual-view-check-") as td:
        zpath = Path(td) / "owner.npz"
        shutil.copy2(npzp, zpath)
        import zipfile
        with zipfile.ZipFile(zpath, "r") as zf:
            if zf.read(rel["member"]) != npyp.read_bytes():
                raise RuntimeError("NPZ member != external NPY")

    remove = {tab["csv_path"], tab["jsonl_path"], rel["npy_path"], rel["npz_path"]}
    stripped = work / "stripped"
    I._copy_without(source, stripped, remove)
    base = work / "base.cmpct"
    PRODUCT.build(stripped, base)

    npydir = work / "npy-source"
    npydir.mkdir(parents=True)
    shutil.copy2(npyp, npydir / npyp.name)
    npya = work / "npy.cmpct"
    PRODUCT.build(npydir, npya)
    if dict(PRODUCT.strong_verify(npya)).get("ok") is False:
        raise RuntimeError("NPY owner strong verify failed")

    npz_raw = npzp.read_bytes()
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "segment_bytes": SEGMENT_BYTES,
        "members": {
            "csv": {"path": tab["csv_path"], "sha256": _sha_hex(csvp.read_bytes()), **I._stat_record(csvp)},
            "jsonl": {"path": tab["jsonl_path"], "sha256": _sha_hex(jsonp.read_bytes()), **I._stat_record(jsonp)},
            "npy": {"path": rel["npy_path"], "sha256": _sha_hex(npyp.read_bytes()), **I._stat_record(npyp)},
            "npz": {"path": rel["npz_path"], "sha256": _sha_hex(npz_raw), **I._stat_record(npzp)},
        },
        "locality_contract": "cold-authenticated-fixed-segment-merkle-v1",
        "npz_relation": {"npy_path": rel["npy_path"], "npz_path": rel["npz_path"], "member": rel["member"]},
    }
    return _write_bundle(out, base, npya, tcol, npz_raw, manifest)


def _extract_candidate(bundle: Path, out: Path) -> dict:
    mraw = (bundle / "manifest.json").read_bytes()
    m = json.loads(mraw)
    meta = (bundle / "npz.meta").read_bytes()
    expected_auth = MAGIC + _sha(mraw) + _sha((bundle / "base.cmpct").read_bytes()) + _sha((bundle / "npy.cmpct").read_bytes()) + _sha((bundle / "owner.tcol").read_bytes()) + _sha(meta)
    if (bundle / "auth.bin").read_bytes() != expected_auth:
        raise ValueError("dual-view bundle authentication failed")
    npz_raw = (bundle / "owner.npz").read_bytes()
    levels, rebuilt_meta, _tree = _merkle(npz_raw)
    if rebuilt_meta != meta:
        raise ValueError("NPZ Merkle root mismatch")

    sv_base = dict(PRODUCT.strong_verify(bundle / "base.cmpct"))
    sv_npy = dict(PRODUCT.strong_verify(bundle / "npy.cmpct"))
    if sv_base.get("ok") is False or sv_npy.get("ok") is False:
        raise RuntimeError("base/NPY strong verify failed")
    PRODUCT.extract(bundle / "base.cmpct", out)
    csv_raw, json_raw = I._owner_raw((bundle / "owner.tcol").read_bytes())
    with tempfile.TemporaryDirectory(prefix="r4-dual-view-npy-") as td:
        td = Path(td)
        PRODUCT.extract(bundle / "npy.cmpct", td)
        npy_raw = (td / Path(m["members"]["npy"]["path"]).name).read_bytes()
    payloads = {"csv": csv_raw, "jsonl": json_raw, "npy": npy_raw, "npz": npz_raw}
    for kind, raw in payloads.items():
        md = m["members"][kind]
        if _sha_hex(raw) != md["sha256"]:
            raise RuntimeError(f"{kind} hash mismatch")
        p = out / md["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        os.chmod(p, int(md["mode"]))
        os.utime(p, ns=(int(md["mtime_ns"]), int(md["mtime_ns"])))
    return {"tree_sha256": PRODUCT.treehash(out), "base_strong_verify": sv_base, "npy_strong_verify": sv_npy, "npz_merkle_root": levels[-1][0].hex()}


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
    expected_tree = PRODUCT.treehash(source)

    ordinary = work / "ordinary.cmpct"
    b0 = _cpu(); w0 = time.perf_counter(); PRODUCT.build(source, ordinary); ordinary_wall = time.perf_counter() - w0; ordinary_cpu = _cpu_delta(_cpu(), b0)

    mode2_bundle = work / "mode2"
    b0 = _cpu(); w0 = time.perf_counter(); mode2_stats = MODE2._build(source, mode2_bundle, work / "mode2-work"); mode2_wall = time.perf_counter() - w0; mode2_cpu = _cpu_delta(_cpu(), b0)

    candidate = work / "dual-view"
    b0 = _cpu(); w0 = time.perf_counter(); cand = _build_candidate(source, candidate, work / "dual-view-work"); cand_wall = time.perf_counter() - w0; cand_cpu = _cpu_delta(_cpu(), b0)
    verify = _extract_candidate(candidate, work / "extract")
    if verify["tree_sha256"] != expected_tree:
        raise RuntimeError("dual-view semantic tree mismatch")

    npz_raw = (source / DUAL._npz_relation(source)["accepted"]["npz_path"]).read_bytes()
    points = sorted(set([0, max(0, len(npz_raw) // 2 - RANGE_BYTES // 2), max(0, len(npz_raw) - RANGE_BYTES), max(0, SEGMENT_BYTES - RANGE_BYTES // 2)]))
    reads = []
    for start in points:
        length = min(RANGE_BYTES, len(npz_raw) - start)
        got, stats = _cold_authenticated_range(candidate, start, length)
        if got != npz_raw[start:start + length]:
            raise RuntimeError("selective NPZ range mismatch")
        reads.append({"start": start, **stats})
    max_amp = max(row["amplification"] for row in reads)

    # Hostile corruption: a touched NPZ data byte must be rejected by the Merkle proof.
    target = len(npz_raw) // 2
    p = candidate / "owner.npz"
    with open(p, "r+b") as f:
        f.seek(target); old = f.read(1); f.seek(target); f.write(bytes([old[0] ^ 1])); f.flush(); os.fsync(f.fileno())
    corruption_rejected = False
    try:
        _cold_authenticated_range(candidate, max(0, target - RANGE_BYTES // 2), min(RANGE_BYTES, len(npz_raw)))
    except ValueError:
        corruption_rejected = True
    finally:
        with open(p, "r+b") as f:
            f.seek(target); f.write(old)
    if not corruption_rejected:
        raise RuntimeError("NPZ corruption was not rejected")

    candidate_bytes = cand["stored_bytes"]
    mode2_bytes = mode2_stats["stored_bytes"]
    margin_v029 = ACCEPTED_V029_ANALYTICS - candidate_bytes
    supported = candidate_bytes < ACCEPTED_V029_ANALYTICS and max_amp <= 8.0 and corruption_rejected
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "tree_sha256": expected_tree,
        "ordinary_v030_bytes": ordinary.stat().st_size,
        "mode2_bytes": mode2_bytes,
        "candidate_bytes": candidate_bytes,
        "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
        "candidate_saving_vs_ordinary_v030_bytes": ordinary.stat().st_size - candidate_bytes,
        "candidate_extra_vs_mode2_bytes": candidate_bytes - mode2_bytes,
        "candidate_margin_vs_v029_bytes": margin_v029,
        "ordinary_create_wall_s": ordinary_wall,
        "ordinary_create_cpu": ordinary_cpu,
        "mode2_create_wall_s": mode2_wall,
        "mode2_create_cpu": mode2_cpu,
        "candidate_create_wall_s": cand_wall,
        "candidate_create_cpu": cand_cpu,
        "process_peak_rss_kib_diagnostic": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "candidate": cand,
        "verify": verify,
        "selective_npz_reads": reads,
        "max_cold_authenticated_npz_amplification": max_amp,
        "corruption_rejected": corruption_rejected,
        "hypothesis": {
            "exact_tree_reconstruction": verify["tree_sha256"] == expected_tree,
            "dual_view_stays_below_v029_analytics": candidate_bytes < ACCEPTED_V029_ANALYTICS,
            "cold_authenticated_npz_range_le_8x": max_amp <= 8.0,
            "corruption_rejected": corruption_rejected,
            "supported_for_next_hardening": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "same_semantic_tree_verified": True,
            "fully_charged_second_npz_view": True,
            "fixed_segment_bytes": SEGMENT_BYTES,
            "cold_read_includes_auth_meta_manifest_and_merkle_proof": True,
            "ordinary_npy_owner_locality_not_remeasured_here": True,
            "no_threshold_sweep": True,
        },
        "next_if_supported": "replace modeled research wrapper with file-backed product prototype and independently verify NPY plus NPZ locality/recovery/native semantics before any promotion",
        "next_if_falsified": "preserve negative; design a smaller authenticated restart-state/chunk-ownership representation instead of weakening the <=8x locality law",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-mode2-dual-view-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-mode2-dual-view.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({
        "ordinary_v030_bytes": d["ordinary_v030_bytes"],
        "mode2_bytes": d["mode2_bytes"],
        "candidate_bytes": d["candidate_bytes"],
        "accepted_v029_bytes": d["accepted_v029_bytes"],
        "candidate_extra_vs_mode2_bytes": d["candidate_extra_vs_mode2_bytes"],
        "candidate_margin_vs_v029_bytes": d["candidate_margin_vs_v029_bytes"],
        "max_cold_authenticated_npz_amplification": d["max_cold_authenticated_npz_amplification"],
        "corruption_rejected": d["corruption_rejected"],
        "components": d["candidate"]["component_bytes"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()

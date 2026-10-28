from __future__ import annotations

"""Research-only dependency-free productization oracle for G04 delimiter inverse.

The gifted NumPy oracle proved large headroom from reconstructing DGO1 directly into one contiguous output.
This follow-up asks whether the same ownership change can be realized with only CPython's bytearray extended-slice
engine. Contiguous runs of equal-length active segments are scattered with one C-level strided slice assignment;
no per-segment output buffers are allocated.

This is still an oracle, not product code. Exact byte identity, CRC/SHA identity and the unchanged DGO1 bounds are
mandatory. The result earns zero release credit until deliberately promoted and re-measured through the complete
shipping product.
"""

import argparse
import binascii
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-stdlib-scatter-oracle-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPS = 15


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    p = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"child failed {p.returncode}: {p.stderr}\n{p.stdout}")
    return json.loads([line for line in p.stdout.splitlines() if line.strip()][-1])


def candidate_inverse(O, encoded: bytes, logical_size: int, *, diagnostics: dict | None = None) -> bytes:
    if not encoded.startswith(b"DGO1") or len(encoded) < 6 or logical_size < 0 or logical_size > O.MAX_OVERLAY_RECORD:
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")

    lengths: list[int] = []
    logical_members = 0
    max_len = 0
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
        max_len = max(max_len, length)
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    if count * max_len > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    starts = [0] * count
    cursor = 0
    for index, length in enumerate(lengths):
        starts[index] = cursor
        cursor += length
        if index + 1 < count:
            cursor += 1
    if cursor != logical_size:
        raise RuntimeError("Geometry overlay delimiter output-shape mismatch")

    out = bytearray(logical_size)
    for index in range(count - 1):
        out[starts[index] + lengths[index]] = delimiter

    body_cursor = 0
    scatter_runs = 0
    active_cells = 0
    for column in range(max_len):
        index = 0
        while index < count:
            while index < count and lengths[index] <= column:
                index += 1
            if index >= count:
                break
            length = lengths[index]
            first = index
            index += 1
            while index < count and lengths[index] == length:
                index += 1
            run_len = index - first
            # Every row in this equal-length run is active because length > column. Consecutive logical row
            # starts are exactly length+1 bytes apart, so bytearray's extended-slice assignment performs the
            # scatter in C while preserving original segment order.
            target_start = starts[first] + column
            target_stop = starts[index - 1] + column + 1
            source_end = body_cursor + run_len
            if source_end > len(body):
                raise RuntimeError("Geometry overlay delimiter short body")
            out[target_start:target_stop:length + 1] = body[body_cursor:source_end]
            body_cursor = source_end
            scatter_runs += 1
            active_cells += run_len
    if body_cursor != len(body) or active_cells != logical_members:
        raise RuntimeError("Geometry overlay delimiter trailing/body accounting mismatch")
    if diagnostics is not None:
        diagnostics.update({
            "scatter_runs": scatter_runs,
            "active_cells": active_cells,
            "average_cells_per_scatter": active_cells / max(scatter_runs, 1),
            "max_segment_length": max_len,
            "unique_segment_lengths": len(set(lengths)),
        })
    return bytes(out)


def run(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as CANON

    R = CANON.POLICY.R
    O = R.G04.O
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]
    archive = work_root / "v030.cmpct"
    pack = _json_child([
        sys.executable, str(PERF.WORKER), "--engine", "v030", "--op", "pack",
        "--source", str(source), "--archive", str(archive),
    ])
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError("ML target no longer selects g04-overlay")

    with CANON.C._revision25_profile_context():
        session = R._G04Session(archive)
        try:
            ids = [i for i, transform in enumerate(session.transforms) if transform and transform[0] == "delimiter"]
            if len(ids) != 1:
                raise RuntimeError(f"expected exactly one delimiter record, got {ids}")
            rid = ids[0]
            rel = session.offsets[rid]
            session.stream.seek(session.record_start + rel)
            header = session.stream.read(R.PH.size)
            codec, usize, csize, crc, expected_sha = R.PH.unpack(header)
            payload = session.stream.read(csize)
            if R.H(payload) != session.leaves[rid]:
                raise RuntimeError("payload authentication drift")
            if codec != R.G04.O.CODEC_ZSTD:
                raise RuntimeError(f"delimiter record codec drift: {codec}")
            encoded = R.G04.O.zd(payload, usize)
            descriptor = session.transforms[rid]
            logical_size = int(descriptor[2])
        finally:
            session.close()

    baseline = O.delimiter_inverse(encoded, logical_size)
    diag: dict = {}
    candidate = candidate_inverse(O, encoded, logical_size, diagnostics=diag)
    if candidate != baseline:
        raise RuntimeError("candidate inverse byte mismatch")
    if (binascii.crc32(candidate) & 0xFFFFFFFF) != crc or R.H(candidate) != expected_sha:
        raise RuntimeError("candidate inverse integrity mismatch")

    current_times: list[float] = []
    candidate_times: list[float] = []
    for rep in range(REPS):
        order = (
            ("current", lambda: O.delimiter_inverse(encoded, logical_size)),
            ("candidate", lambda: candidate_inverse(O, encoded, logical_size)),
        )
        if rep % 2:
            order = tuple(reversed(order))
        for name, fn in order:
            t0 = time.perf_counter()
            got = fn()
            dt = time.perf_counter() - t0
            if got != baseline:
                raise RuntimeError("timed inverse mismatch")
            (current_times if name == "current" else candidate_times).append(dt)

    cm = statistics.median(current_times)
    nm = statistics.median(candidate_times)
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle-dependency-free-productization",
        "product_release_credit": False,
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "record_id": rid,
            "codec": "zstd",
            "logical_size": logical_size,
            "encoded_bytes": len(encoded),
            "compressed_payload_bytes": len(payload),
            "delimiter": int(descriptor[1]),
            "segment_count": int(O._get_varint(encoded, 5)[0]),
            "repetitions_each": REPS,
            "same_exact_encoded_bytes": True,
            "candidate_bytes_equal_current": True,
            "candidate_crc_sha_match_archive": True,
            "single_contiguous_output_buffer": True,
            "third_party_runtime_dependency_added": False,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
        "shape": diag,
        "comparison": {
            "current_median_s": cm,
            "candidate_median_s": nm,
            "speedup_x": cm / max(nm, 1e-12),
            "time_reduction_fraction": (cm - nm) / max(cm, 1e-12),
            "saved_s": cm - nm,
            "current_samples_s": current_times,
            "candidate_samples_s": candidate_times,
        },
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-stdlib-scatter-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-stdlib-scatter.json"))
    args = ap.parse_args()
    try:
        payload = run(args.work_root)
    except BaseException as exc:
        _write(args.output, {
            "engine": ENGINE,
            "status": "HARNESS_FAILURE",
            "evidence_class": "research-oracle-dependency-free-productization",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        })
        raise
    _write(args.output, payload)
    print(json.dumps({"shape": payload["shape"], "comparison": payload["comparison"]}, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Research-only headroom oracle for the G04 delimiter inverse allocation/layout cost.

The preceding exact-head block/strided-slice oracle preserved the canonical per-segment bytearray layout and
recovered only ~5% of inverse time. This oracle deliberately gifts NumPy as an experimental vector/scatter engine
to test a different causal hypothesis: the remaining cost is dominated by Python object/layout work from tens of
thousands of segment buffers rather than by the transform grammar itself.

The candidate reconstructs one exact DGO1 record into one contiguous logical output buffer. It changes no product
code, archive bytes, grammar, admission, integrity rule, locality rule or release threshold and earns zero product
or release credit. A large exact win would justify implementing the same ownership/layout idea in the shared native
core; a small win would falsify allocation/layout as the next useful owner.
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

import numpy as np

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-numpy-scatter-oracle-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPS = 15


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    p = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"child failed {p.returncode}: {p.stderr}\n{p.stdout}")
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])


def candidate_inverse(O, encoded: bytes, logical_size: int) -> bytes:
    if not encoded.startswith(b"DGO1") or len(encoded) < 6 or logical_size < 0 or logical_size > O.MAX_OVERLAY_RECORD:
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")

    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    max_len = max(lengths, default=0)
    if count * max_len > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    lengths_np = np.asarray(lengths, dtype=np.int64)
    starts = np.empty(count, dtype=np.int64)
    if count:
        starts[0] = 0
        if count > 1:
            starts[1:] = np.cumsum(lengths_np[:-1] + 1, dtype=np.int64)
    out = np.empty(logical_size, dtype=np.uint8)
    if count > 1:
        out[starts[:-1] + lengths_np[:-1]] = delimiter

    body_np = np.frombuffer(body, dtype=np.uint8)
    cursor = 0
    # DGO1 body order is column-major over the still-active rows. The grammar caps max_len, so this loop is
    # bounded by the transform's existing cell-work law while every per-row scatter executes in native code.
    for column in range(max_len):
        active = np.flatnonzero(lengths_np > column)
        width = int(active.size)
        end = cursor + width
        if end > body_np.size:
            raise RuntimeError("Geometry overlay delimiter short body")
        out[starts[active] + column] = body_np[cursor:end]
        cursor = end
    if cursor != body_np.size:
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return out.tobytes()


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
    candidate = candidate_inverse(O, encoded, logical_size)
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
        "evidence_class": "research-oracle-gifted-vector-engine",
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
            "segment_count": int(encoded.startswith(b"DGO1") and O._get_varint(encoded, 5)[0]),
            "repetitions_each": REPS,
            "same_exact_encoded_bytes": True,
            "candidate_bytes_equal_current": True,
            "candidate_crc_sha_match_archive": True,
            "single_contiguous_output_buffer": True,
            "gifted_numpy_vector_scatter": True,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
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
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-numpy-scatter-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-numpy-scatter.json"))
    args = ap.parse_args()
    try:
        payload = run(args.work_root)
    except BaseException as exc:
        _write(args.output, {
            "engine": ENGINE,
            "status": "HARNESS_FAILURE",
            "evidence_class": "research-oracle-gifted-vector-engine",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        })
        raise
    _write(args.output, payload)
    print(json.dumps(payload["comparison"], indent=2))


if __name__ == "__main__":
    main()

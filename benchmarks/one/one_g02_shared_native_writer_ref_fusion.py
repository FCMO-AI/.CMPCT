"""ONE-G0.2 shared-native writer final-ref fusion rehabilitation falsifier.

Frozen by ONE_G02_SHARED_NATIVE_WRITER_REF_FUSION_PREREG_2026-09-06.md.
The matrix, timing boundary and original transfer gates are intentionally reused
rather than retuned after observing the failed seed.
"""
from __future__ import annotations

import contextlib
import ctypes
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

import benchmarks.one.one_g02_shared_native_writer_transfer as seed
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import Segment


FRAGMENTED_GAIN_RETENTION_MAX = 0.15
MATURE_MIN = 16 * 1024


def _build_writer_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-writer-ref-fused-")
    lib = Path(td.name) / "libnativewriter_ref_fused.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "native" / "one_g02_shared_native_writer_ref_fused.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_native_writer
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
        ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t),
    ]
    fn.restype = ctypes.c_int
    free_fn = c.one_g02_native_writer_free
    free_fn.argtypes = [ctypes.c_void_p]
    free_fn.restype = None
    return fn, free_fn, td


def run() -> None:
    # Reuse the already-frozen transfer harness wholesale.  The only candidate
    # change is which native C implementation backs the same ABI.
    original_builder = seed._build_writer_native
    captured = io.StringIO()
    seed_exit = 0
    try:
        seed._build_writer_native = _build_writer_native
        try:
            with contextlib.redirect_stdout(captured):
                seed.run()
        except SystemExit as exc:
            seed_exit = int(exc.code or 0)
    finally:
        seed._build_writer_native = original_builder

    raw = captured.getvalue().strip()
    if not raw:
        raise RuntimeError("seed transfer harness produced no JSON result")
    result = json.loads(raw)

    mature_fragmented = [
        float(row["candidate_over_baseline"])
        for row in result["rows"]
        if row["productive"]
        and int(row["relation_bytes"]) >= MATURE_MIN
        and row["case"] == "fragmented_every96"
    ]
    fragmented_median = float(statistics.median(mature_fragmented))
    gain_retained = fragmented_median <= FRAGMENTED_GAIN_RETENTION_MAX

    original_decision = result["decision"]
    original_gate_pass = original_decision == "advance_shared_native_writer_transfer" and seed_exit == 0
    decision = (
        "advance_shared_native_writer_ref_fusion"
        if original_gate_pass and gain_retained
        else "reject_shared_native_writer_ref_fusion"
    )

    result.update({
        "schema": "cmpct-one-g02-shared-native-writer-ref-fusion-v1",
        "claim_boundary": (
            "frozen adjacent-version shared-native writer with generic one-level "
            "Segment-to-concat ref fusion only; product/authenticated placement/RSS/"
            "comparator authority excluded"
        ),
        "seed_transfer_gate_decision_under_ref_fusion": original_decision,
        "fragmented_every96_mature_median_ratio": fragmented_median,
        "fragmented_gain_retention_max": FRAGMENTED_GAIN_RETENTION_MAX,
        "fragmented_gain_retained": gain_retained,
        "decision": decision,
    })
    print(json.dumps(result, indent=2, sort_keys=True))
    if decision != "advance_shared_native_writer_ref_fusion":
        raise SystemExit(1)


if __name__ == "__main__":
    run()

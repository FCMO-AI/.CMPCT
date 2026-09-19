from __future__ import annotations

"""One-shot causal ablation: level-19 source-size default searchLog minus one.

Mission: docs/V030_ANALYTICS_SEARCHLOG6_ABLATION_MISSION_2026-09-12.md
Research-only. This file intentionally contains no parameter sweep.
"""

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

import msgpack

from benchmarks import v030_analytics_reusable_zstd_context_referee as REUSE
from experiments import entropygraph_v025 as V25

ROUNDS = 3
EXPECTED = 45
LEVEL = 19
MAX_GROWTH = 49_152
MAX_CPU_RATIO = 0.80
ZSTD_C_COMPRESSION_LEVEL = 100
ZSTD_C_SEARCH_LOG = 104


class ZSTDCompressionParameters(ctypes.Structure):
    _fields_ = [
        ("windowLog", ctypes.c_uint),
        ("chainLog", ctypes.c_uint),
        ("hashLog", ctypes.c_uint),
        ("searchLog", ctypes.c_uint),
        ("minMatch", ctypes.c_uint),
        ("targetLength", ctypes.c_uint),
        ("strategy", ctypes.c_int),
    ]


def _rss_kib() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value // 1024 if sys.platform == "darwin" else value


def _candidate_compress(raw: bytes) -> tuple[bytes, dict]:
    z = V25.z
    z.ZSTD_getCParams.argtypes = [ctypes.c_int, ctypes.c_ulonglong, ctypes.c_size_t]
    z.ZSTD_getCParams.restype = ZSTDCompressionParameters
    z.ZSTD_createCCtx.argtypes = []
    z.ZSTD_createCCtx.restype = ctypes.c_void_p
    z.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
    z.ZSTD_freeCCtx.restype = ctypes.c_size_t
    z.ZSTD_CCtx_setParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    z.ZSTD_CCtx_setParameter.restype = ctypes.c_size_t
    z.ZSTD_CCtx_setPledgedSrcSize.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong]
    z.ZSTD_CCtx_setPledgedSrcSize.restype = ctypes.c_size_t
    z.ZSTD_compress2.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    z.ZSTD_compress2.restype = ctypes.c_size_t
    z.ZSTD_isError.argtypes = [ctypes.c_size_t]
    z.ZSTD_isError.restype = ctypes.c_uint
    z.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
    z.ZSTD_getErrorName.restype = ctypes.c_char_p

    def check(code: int) -> int:
        if z.ZSTD_isError(code):
            raise RuntimeError(z.ZSTD_getErrorName(code).decode())
        return int(code)

    defaults = z.ZSTD_getCParams(LEVEL, len(raw), 0)
    candidate_search = max(1, int(defaults.searchLog) - 1)
    ctx = z.ZSTD_createCCtx()
    if not ctx:
        raise RuntimeError("ZSTD_createCCtx failed")
    try:
        check(z.ZSTD_CCtx_setParameter(ctx, ZSTD_C_COMPRESSION_LEVEL, LEVEL))
        check(z.ZSTD_CCtx_setPledgedSrcSize(ctx, len(raw)))
        check(z.ZSTD_CCtx_setParameter(ctx, ZSTD_C_SEARCH_LOG, candidate_search))
        cap = int(z.ZSTD_compressBound(len(raw)))
        dst = ctypes.create_string_buffer(cap)
        src = ctypes.c_char_p(raw)
        n = check(z.ZSTD_compress2(ctx, dst, cap, src, len(raw)))
        payload = dst.raw[:n]
    finally:
        check(z.ZSTD_freeCCtx(ctx))
    return payload, {
        "usize": len(raw),
        "default_windowLog": int(defaults.windowLog),
        "default_chainLog": int(defaults.chainLog),
        "default_hashLog": int(defaults.hashLog),
        "default_searchLog": int(defaults.searchLog),
        "candidate_searchLog": candidate_search,
        "default_minMatch": int(defaults.minMatch),
        "default_targetLength": int(defaults.targetLength),
        "default_strategy": int(defaults.strategy),
    }


def _worker(fixture: Path, engine: str, output: Path) -> None:
    packs = msgpack.unpackb(fixture.read_bytes(), raw=False)
    if len(packs) != EXPECTED:
        raise RuntimeError(f"fixture population drift {len(packs)} != {EXPECTED}")
    rss0 = _rss_kib()
    rows = []
    c0 = time.process_time(); w0 = time.perf_counter()
    for row in packs:
        raw = bytes(row["raw"])
        if engine == "baseline":
            payload = V25.zc(raw, LEVEL)
            params = None
        elif engine == "searchlog_minus_one":
            payload, params = _candidate_compress(raw)
        else:
            raise RuntimeError(engine)
        decoded = V25.zd(payload, len(raw))
        if decoded != raw:
            raise RuntimeError("candidate decode drift")
        rows.append({
            "sha256": bytes(row["sha256"]).hex(),
            "usize": len(raw),
            "csize": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "params": params,
        })
    cpu = time.process_time() - c0; wall = time.perf_counter() - w0
    output.write_text(json.dumps({
        "engine": engine, "pack_count": len(rows), "input_bytes": sum(r["usize"] for r in rows),
        "output_bytes": sum(r["csize"] for r in rows), "cpu_s": cpu, "wall_s": wall,
        "rss_baseline_kib": rss0, "rss_peak_kib": _rss_kib(), "rows": rows,
    }, indent=2) + "\n")


def _run_worker(fixture: Path, root: Path, engine: str, ri: int) -> dict:
    out = root / f"{ri}-{engine}.json"
    cp = subprocess.run([
        sys.executable, str(Path(__file__).resolve()), "--worker", "--fixture", str(fixture.resolve()),
        "--engine", engine, "--worker-output", str(out.resolve()),
    ], text=True, capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"{engine}/{ri} failed rc={cp.returncode}\n{cp.stdout}\n{cp.stderr}")
    return json.loads(out.read_text())


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    fixture, prep = REUSE._prepare_fixture(work_root)
    samples = {"baseline": [], "searchlog_minus_one": []}
    for ri in range(ROUNDS):
        order = ["baseline", "searchlog_minus_one"]
        if ri % 2: order.reverse()
        for engine in order:
            samples[engine].append(_run_worker(fixture, work_root, engine, ri))

    summaries = {}
    for engine, rr in samples.items():
        out_sizes = {int(r["output_bytes"]) for r in rr}
        identities = {tuple((x["sha256"], x["usize"], x["csize"], x["payload_sha256"]) for x in r["rows"]) for r in rr}
        if len(out_sizes) != 1 or len(identities) != 1:
            raise RuntimeError(f"{engine} nondeterminism")
        summaries[engine] = {
            "output_bytes": next(iter(out_sizes)),
            "median_cpu_s": statistics.median(float(r["cpu_s"]) for r in rr),
            "median_wall_s": statistics.median(float(r["wall_s"]) for r in rr),
            "median_peak_rss_kib": statistics.median(int(r["rss_peak_kib"]) for r in rr),
            "median_incremental_rss_kib": statistics.median(max(0, int(r["rss_peak_kib"])-int(r["rss_baseline_kib"])) for r in rr),
            "rows": rr[0]["rows"], "raw": rr,
        }

    # Verify exactly one compression parameter differs from source-size-specific level-19 defaults.
    param_profiles = {}
    for row in summaries["searchlog_minus_one"]["rows"]:
        p = row["params"]
        if p["candidate_searchLog"] != max(1, p["default_searchLog"] - 1):
            raise RuntimeError("SearchLog delta contract drift")
        key = str(row["usize"])
        profile = {k: v for k, v in p.items() if k != "usize"}
        if key in param_profiles and param_profiles[key] != profile:
            raise RuntimeError("source-size parameter profile drift")
        param_profiles[key] = profile

    growth = summaries["searchlog_minus_one"]["output_bytes"] - summaries["baseline"]["output_bytes"]
    cpu_ratio = summaries["searchlog_minus_one"]["median_cpu_s"] / summaries["baseline"]["median_cpu_s"]
    wall_ratio = summaries["searchlog_minus_one"]["median_wall_s"] / summaries["baseline"]["median_wall_s"]
    gate = {
        "exact_decode_all_payloads": True,
        "only_searchlog_minus_one": True,
        "output_growth_at_most_49152": growth <= MAX_GROWTH,
        "cpu_ratio_at_most_0_80": cpu_ratio <= MAX_CPU_RATIO,
    }
    verdict = "INTEGRATE_WITH_EARNED_BYTEPLANE4_MARGIN" if all(gate.values()) else "RETIRE_SEARCHLOG_MINUS_ONE"
    return {
        "schema": "cmpct-v030-analytics-searchlog-minus-one-ablation-v1", "release_credit": False,
        "experiment_valid": True, "rounds": ROUNDS, "fixture": prep, "level": LEVEL,
        "engines": summaries, "candidate_output_growth_bytes": growth, "candidate_over_baseline_cpu": cpu_ratio,
        "candidate_over_baseline_wall": wall_ratio, "source_size_parameter_profiles": param_profiles,
        "gate": gate, "verdict": verdict,
        "contract": {"frozen_45_pack_population": True, "single_parameter_ablation": "searchLog-1",
                     "same_loaded_libzstd": True, "fresh_child_per_engine": True,
                     "candidate_decode_exact": True, "no_archive_or_release_credit": True,
                     "no_parameter_sweep": True},
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-searchlog6-work")); ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-searchlog6.json")); ap.add_argument("--worker", action="store_true"); ap.add_argument("--fixture", type=Path); ap.add_argument("--engine", choices=("baseline","searchlog_minus_one")); ap.add_argument("--worker-output", type=Path); args = ap.parse_args()
    if args.worker:
        if args.fixture is None or args.engine is None or args.worker_output is None: raise SystemExit("worker args missing")
        _worker(args.fixture, args.engine, args.worker_output); return
    r = run(args.work_root); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(r, indent=2)+"\n")
    print(json.dumps({"verdict":r["verdict"],"growth_bytes":r["candidate_output_growth_bytes"],"cpu_ratio":r["candidate_over_baseline_cpu"],"wall_ratio":r["candidate_over_baseline_wall"],"gate":r["gate"]}, indent=2), flush=True)


if __name__ == "__main__": main()

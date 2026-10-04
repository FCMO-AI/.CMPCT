from __future__ import annotations

"""Referee for exact reusable-libzstd context acceleration on frozen Analytics packs.

Mission: docs/V030_ANALYTICS_REUSABLE_ZSTD_CONTEXT_MISSION_2026-09-12.md
Research-only: no archive/release credit. Green CI means only that the receipt is valid.
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

from benchmarks import v030_analytics_proof_directed_admission_oracle as ORACLE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
MIN_SIZE = 256 * 1024
MAX_CHEAP_RATIO_PPM = 700_000
LEVEL = 19
ROUNDS = 3
ENGINES = ("oneshot", "reusable_cctx")
EXPECTED_ADMITTED = 45


def _rss_kib() -> int:
    v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return v // 1024 if sys.platform == "darwin" else v


def _prepare_fixture(work_root: Path) -> tuple[Path, dict]:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_reuse_cctx_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_reuse_cctx_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work_root / "normalized")
    build = ORACLE._build(stage, work_root / "level-15", 15)

    archive = work_root / "level-15" / "candidate.cmpnx5"
    V25.OUT = archive
    f, meta, po = V25.open_ar()
    try:
        stream_pi = {int(pi) for _so, pi, _ln in meta.get("stream_packs", [])}
        admitted = []
        ordinary_candidates = 0
        for pi, entry in enumerate(po):
            if pi in stream_pi:
                continue
            ordinary_candidates += 1
            _off, _codec, usize, csize, _crc, hh = entry
            raw = ORACLE._decode_pack(f, entry)
            ratio_ppm = int(1_000_000 * int(csize) / max(1, int(usize)))
            if int(usize) >= MIN_SIZE and ratio_ppm <= MAX_CHEAP_RATIO_PPM:
                admitted.append({"sha256": bytes(hh), "raw": raw, "usize": int(usize), "l15_csize": int(csize), "ratio_ppm": ratio_ppm})
    finally:
        f.close()
    if len(admitted) != EXPECTED_ADMITTED:
        raise RuntimeError(f"frozen admission population drift: {len(admitted)} != {EXPECTED_ADMITTED}")

    fixture = work_root / "admitted-packs.msgpack"
    fixture.write_bytes(msgpack.packb(admitted, use_bin_type=True))
    return fixture, {
        "l15_archive_bytes": int(build["archive_bytes"]),
        "pack_count": int(build["build_stats"]["packs"]),
        "ordinary_level19_candidate_count": ordinary_candidates,
        "admitted_count": len(admitted),
        "admitted_input_bytes": sum(x["usize"] for x in admitted),
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
    }


class ReusableCCtx:
    def __init__(self, max_input: int):
        z = V25.z
        z.ZSTD_createCCtx.argtypes = []
        z.ZSTD_createCCtx.restype = ctypes.c_void_p
        z.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
        z.ZSTD_freeCCtx.restype = ctypes.c_size_t
        z.ZSTD_compressCCtx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        z.ZSTD_compressCCtx.restype = ctypes.c_size_t
        z.ZSTD_isError.argtypes = [ctypes.c_size_t]
        z.ZSTD_isError.restype = ctypes.c_uint
        z.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
        z.ZSTD_getErrorName.restype = ctypes.c_char_p
        self.z = z
        self.ctx = z.ZSTD_createCCtx()
        if not self.ctx:
            raise RuntimeError("ZSTD_createCCtx failed")
        cap = int(z.ZSTD_compressBound(max_input))
        self.dst = ctypes.create_string_buffer(cap)
        self.cap = cap

    def close(self) -> None:
        if self.ctx:
            code = int(self.z.ZSTD_freeCCtx(self.ctx))
            if self.z.ZSTD_isError(code):
                raise RuntimeError(self.z.ZSTD_getErrorName(code).decode())
            self.ctx = None

    def compress(self, raw: bytes, level: int) -> bytes:
        src = ctypes.c_char_p(raw)
        n = int(self.z.ZSTD_compressCCtx(self.ctx, self.dst, self.cap, src, len(raw), int(level)))
        if self.z.ZSTD_isError(n):
            raise RuntimeError(self.z.ZSTD_getErrorName(n).decode())
        return self.dst.raw[:n]


def _worker(fixture: Path, engine: str, output: Path) -> None:
    packs = msgpack.unpackb(fixture.read_bytes(), raw=False)
    raws = [bytes(row["raw"]) for row in packs]
    rss0 = _rss_kib()
    out_hashes = []
    total_out = 0
    c0 = time.process_time(); w0 = time.perf_counter()
    runner = None
    try:
        if engine == "reusable_cctx":
            runner = ReusableCCtx(max(map(len, raws), default=0))
        for raw in raws:
            comp = V25.zc(raw, LEVEL) if engine == "oneshot" else runner.compress(raw, LEVEL)
            out_hashes.append(hashlib.sha256(comp).hexdigest())
            total_out += len(comp)
    finally:
        if runner is not None:
            runner.close()
    cpu = time.process_time() - c0; wall = time.perf_counter() - w0
    rss1 = _rss_kib()
    output.write_text(json.dumps({
        "engine": engine, "pack_count": len(raws), "input_bytes": sum(map(len, raws)),
        "output_bytes": total_out, "payload_sha256": out_hashes,
        "cpu_s": cpu, "wall_s": wall, "rss_baseline_kib": rss0,
        "rss_peak_kib": rss1, "rss_increment_kib": max(0, rss1-rss0),
    }, indent=2)+"\n")


def _run_worker(fixture: Path, work_root: Path, engine: str, ri: int) -> dict:
    out = work_root / f"{ri}-{engine}.json"
    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", "--fixture", str(fixture.resolve()), "--engine", engine, "--worker-output", str(out.resolve())], text=True, capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"{engine}/{ri} failed rc={cp.returncode}\n{cp.stdout}\n{cp.stderr}")
    return json.loads(out.read_text())


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    fixture, prep = _prepare_fixture(work_root)
    rows = {e: [] for e in ENGINES}
    for ri in range(ROUNDS):
        order = list(ENGINES); order = order[ri % 2:] + order[:ri % 2]
        for e in order:
            rows[e].append(_run_worker(fixture, work_root, e, ri))

    summaries = {}
    for e, rr in rows.items():
        digests = {tuple(r["payload_sha256"]) for r in rr}; outs = {r["output_bytes"] for r in rr}
        if len(digests)!=1 or len(outs)!=1: raise RuntimeError(f"{e} output nondeterminism")
        summaries[e] = {
            "pack_count": rr[0]["pack_count"], "input_bytes": rr[0]["input_bytes"], "output_bytes": next(iter(outs)),
            "payload_sha256": list(next(iter(digests))),
            "median_cpu_s": statistics.median(r["cpu_s"] for r in rr),
            "median_wall_s": statistics.median(r["wall_s"] for r in rr),
            "median_peak_rss_kib": statistics.median(r["rss_peak_kib"] for r in rr),
            "median_incremental_rss_kib": statistics.median(r["rss_increment_kib"] for r in rr),
            "raw": rr,
        }
    exact = summaries["oneshot"]["payload_sha256"] == summaries["reusable_cctx"]["payload_sha256"]
    wall_ratio = summaries["reusable_cctx"]["median_wall_s"] / summaries["oneshot"]["median_wall_s"]
    cpu_ratio = summaries["reusable_cctx"]["median_cpu_s"] / summaries["oneshot"]["median_cpu_s"]
    gate = {"byte_identical_all_payloads": exact, "wall_ratio_at_most_0_80": wall_ratio <= 0.80}
    verdict = "BUILD_REUSABLE_CONTEXT_IN_SELECTIVE_WRITER" if all(gate.values()) else "RETIRE_CONTEXT_REUSE_AS_PRIMARY_SPEED_FIX"
    return {
        "schema":"cmpct-v030-analytics-reusable-zstd-context-referee-v1", "release_credit":False, "experiment_valid":True,
        "target":f"neutral_hostile_v1/{TARGET}", "rounds":ROUNDS,
        "frozen_admission":{"min_raw_bytes":MIN_SIZE,"max_l15_ratio_ppm":MAX_CHEAP_RATIO_PPM},
        "fixture":prep, "engines":summaries, "reusable_over_oneshot_wall":wall_ratio,
        "reusable_over_oneshot_cpu":cpu_ratio, "gate":gate, "verdict":verdict,
        "contract":{"same_loaded_libzstd":True,"same_level":LEVEL,"fresh_process_per_engine":True,
                    "context_creation_timed":True,"fixture_loading_outside_compression_timer":True,
                    "compressed_bytes_must_match":True,"no_archive_or_release_credit":True},
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-analytics-reusable-zstd-work")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-analytics-reusable-zstd.json")); ap.add_argument("--worker",action="store_true"); ap.add_argument("--fixture",type=Path); ap.add_argument("--engine",choices=ENGINES); ap.add_argument("--worker-output",type=Path); args=ap.parse_args()
    if args.worker:
        if None in (args.fixture,args.engine,args.worker_output): raise SystemExit("worker args missing")
        _worker(args.fixture,args.engine,args.worker_output); return
    r=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps({"verdict":r["verdict"],"wall_ratio":r["reusable_over_oneshot_wall"],"cpu_ratio":r["reusable_over_oneshot_cpu"],"gate":r["gate"]},indent=2),flush=True)


if __name__ == "__main__": main()

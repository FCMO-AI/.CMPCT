from __future__ import annotations

"""R4 diagnostic: decompose the density/time jump between Zstd levels 15 and 19.

The Analytics effort frontier showed that level 15 preserves the ZIP-time budget but leaves a large
byte gap, while level 19 nearly recovers the inherited v0.29 floor at prohibitive creation cost. Zstd
levels are bundles of compression parameters, not mechanisms. This oracle freezes the v0.25 structural
representation and measures which level-19 parameter changes actually purchase the missing bytes.

No shipping policy is changed. The experiment has no release credit. A promising hybrid must later be
built/strong-verified as a whole archive and pass held-out hostile controls before it can become a
candidate.
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = ("02_office_workspace", "04_analytics_and_database", "01_developer_repository")
LOW_LEVEL = 15
HIGH_LEVEL = 19
PROBE_LEVEL = 3
MAX_PATH_BYTES = 4096


class CParams(ctypes.Structure):
    _fields_ = [
        ("windowLog", ctypes.c_uint),
        ("chainLog", ctypes.c_uint),
        ("hashLog", ctypes.c_uint),
        ("searchLog", ctypes.c_uint),
        ("minMatch", ctypes.c_uint),
        ("targetLength", ctypes.c_uint),
        ("strategy", ctypes.c_int),
    ]


PARAM_ENUM = {
    "windowLog": 101,
    "hashLog": 102,
    "chainLog": 103,
    "searchLog": 104,
    "minMatch": 105,
    "targetLength": 106,
    "strategy": 107,
}
PARAM_FIELDS = tuple(PARAM_ENUM)

_z = ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so")
_sz = ctypes.c_size_t
_z.ZSTD_getCParams.argtypes = [ctypes.c_int, ctypes.c_ulonglong, _sz]
_z.ZSTD_getCParams.restype = CParams
_z.ZSTD_createCCtx.restype = ctypes.c_void_p
_z.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
_z.ZSTD_CCtx_setParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_z.ZSTD_CCtx_setParameter.restype = _sz
_z.ZSTD_CCtx_setPledgedSrcSize.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong]
_z.ZSTD_CCtx_setPledgedSrcSize.restype = _sz
_z.ZSTD_compressBound.argtypes = [_sz]
_z.ZSTD_compressBound.restype = _sz
_z.ZSTD_compress2.argtypes = [ctypes.c_void_p, ctypes.c_void_p, _sz, ctypes.c_void_p, _sz]
_z.ZSTD_compress2.restype = _sz
_z.ZSTD_isError.argtypes = [_sz]
_z.ZSTD_isError.restype = ctypes.c_uint
_z.ZSTD_getErrorName.argtypes = [_sz]
_z.ZSTD_getErrorName.restype = ctypes.c_char_p


def _check(code: int) -> int:
    if _z.ZSTD_isError(code):
        raise RuntimeError(_z.ZSTD_getErrorName(code).decode("utf-8", "replace"))
    return int(code)


def _params(level: int, n: int) -> dict[str, int]:
    p = _z.ZSTD_getCParams(level, n, 0)
    return {name: int(getattr(p, name)) for name in PARAM_FIELDS}


def _compress_params(raw: bytes, params: dict[str, int]) -> bytes:
    if not raw:
        return b""
    cctx = _z.ZSTD_createCCtx()
    if not cctx:
        raise MemoryError("ZSTD_createCCtx failed")
    try:
        for name in PARAM_FIELDS:
            _check(_z.ZSTD_CCtx_setParameter(cctx, PARAM_ENUM[name], int(params[name])))
        _check(_z.ZSTD_CCtx_setPledgedSrcSize(cctx, len(raw)))
        src = ctypes.create_string_buffer(raw)
        cap = int(_z.ZSTD_compressBound(len(raw)))
        dst = ctypes.create_string_buffer(cap)
        n = _check(_z.ZSTD_compress2(cctx, dst, cap, src, len(raw)))
        return dst.raw[:n]
    finally:
        _z.ZSTD_freeCCtx(cctx)


def _physical(raw_n: int, compressed_n: int) -> int:
    return compressed_n if compressed_n + 8 < raw_n else raw_n


def _variants(raw_n: int) -> dict[str, dict[str, int]]:
    lo = _params(LOW_LEVEL, raw_n)
    hi = _params(HIGH_LEVEL, raw_n)
    out = {"level15": dict(lo), "level19": dict(hi)}
    for field in PARAM_FIELDS:
        p = dict(lo)
        p[field] = hi[field]
        out[f"l15_plus_{field}19"] = p
    # Strategy is the largest qualitative change on medium/large inputs (btultra2 at level 19).
    # Measure interactions explicitly instead of guessing from level numbers.
    for fields in (
        ("strategy", "searchLog"),
        ("strategy", "targetLength"),
        ("strategy", "minMatch"),
        ("strategy", "searchLog", "targetLength"),
        ("strategy", "searchLog", "targetLength", "minMatch"),
        ("strategy", "searchLog", "targetLength", "minMatch", "chainLog"),
    ):
        p = dict(lo)
        for field in fields:
            p[field] = hi[field]
        out["l15_plus_" + "_".join(f + "19" for f in fields)] = p
    for field in PARAM_FIELDS:
        p = dict(hi)
        p[field] = lo[field]
        out[f"l19_minus_{field}19"] = p
    return out


def _prepare(stage: Path, root: Path) -> tuple[Path, float]:
    root.mkdir(parents=True, exist_ok=True)
    profile = root / "profile"
    started = time.perf_counter()
    FS.prepare_profile_tree(
        stage,
        profile,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=PRODUCT.MAX_PROFILE_FILES,
        max_profile_logical_bytes=PRODUCT.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    return profile, time.perf_counter() - started


def _scan(profile: Path, archive: Path) -> tuple[dict[str, dict], float, dict]:
    V25.ROOT = profile
    V25.OUT = archive
    original = V25.zc
    raws: dict[str, dict] = {}

    def capture(raw: bytes, level: int = HIGH_LEVEL) -> bytes:
        if int(level) < HIGH_LEVEL:
            return original(raw, min(int(level), PROBE_LEVEL))
        key = hashlib.sha256(raw).hexdigest()
        rec = raws.setdefault(key, {"raw": raw, "calls": 0})
        rec["calls"] += 1
        return original(raw, LOW_LEVEL)

    V25.zc = capture
    try:
        t = time.perf_counter()
        stats = dict(V25.build())
        elapsed = time.perf_counter() - t
    finally:
        V25.zc = original
    return raws, elapsed, stats


def _verify(profile: Path, archive: Path, out: Path, expected: str) -> float:
    V25.ROOT = profile
    V25.OUT = archive
    t = time.perf_counter()
    result = dict(V25.strong_verify())
    elapsed = time.perf_counter() - t
    if not result.get("ok"):
        raise RuntimeError(f"strong verification failed: {result!r}")
    shutil.rmtree(out, ignore_errors=True)
    V25.extract(out)
    manifest = out.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    decoded = FS.decode_manifest(manifest.read_bytes(), max_path_bytes=MAX_PATH_BYTES, max_entries=PRODUCT.MAX_MANIFEST_ENTRIES)
    FS.restore_manifest_tree(out, decoded)
    actual = PRODUCT.treehash(out)
    if actual != expected:
        raise RuntimeError(f"restored tree mismatch: {actual} != {expected}")
    return elapsed


def _measure_raw(raw: bytes, calls: int) -> dict:
    variants = _variants(len(raw))
    row = {"raw_bytes": len(raw), "calls": calls, "level15_params": variants["level15"], "level19_params": variants["level19"], "variants": {}}
    for name, params in variants.items():
        times = []
        blob = b""
        for _ in range(2):
            t = time.perf_counter()
            blob = _compress_params(raw, params)
            times.append(time.perf_counter() - t)
        if V25.zd(blob, len(raw)) != raw:
            raise RuntimeError(f"parameterized zstd round trip failed: {name}")
        row["variants"][name] = {
            "compressed_bytes": len(blob),
            "physical_payload_bytes": _physical(len(raw), len(blob)),
            "median_compress_s": statistics.median(times),
        }
    # Prove that explicit parameterization reproduces the ordinary library presets exactly.
    for level_name, level in (("level15", LOW_LEVEL), ("level19", HIGH_LEVEL)):
        ordinary = V25.zc(raw, level)
        explicit = _compress_params(raw, variants[level_name])
        if ordinary != explicit:
            raise RuntimeError(f"explicit {level_name} parameters do not reproduce ZSTD_compress preset")
    return row


def _one(name: str, source: Path, accepted_v029: int, work: Path) -> dict:
    stage = EXT._normalized_stage(source, work / name / "normalized")
    expected = PRODUCT.treehash(stage)
    root = work / name / "scan"
    profile, stage_s = _prepare(stage, root)
    archive = root / "level15-fixed.cmpnx5"
    raws, scan_s, build_stats = _scan(profile, archive)
    verify_s = _verify(profile, archive, root / "out", expected)
    archive_bytes = archive.stat().st_size

    measured = []
    for key, rec in raws.items():
        m = _measure_raw(rec["raw"], int(rec["calls"]))
        m["sha256"] = key
        measured.append(m)

    names = sorted(next(iter(measured))["variants"]) if measured else []
    aggregate = {}
    baseline_payload = sum(r["variants"]["level15"]["physical_payload_bytes"] * r["calls"] for r in measured)
    baseline_time = sum(r["variants"]["level15"]["median_compress_s"] * r["calls"] for r in measured)
    for variant in names:
        payload = sum(r["variants"][variant]["physical_payload_bytes"] * r["calls"] for r in measured)
        ctime = sum(r["variants"][variant]["median_compress_s"] * r["calls"] for r in measured)
        predicted_archive = archive_bytes - baseline_payload + payload
        aggregate[variant] = {
            "predicted_archive_bytes": predicted_archive,
            "delta_vs_level15_bytes": predicted_archive - archive_bytes,
            "gap_to_v029_bytes": predicted_archive - accepted_v029,
            "aggregate_final_compress_s": ctime,
            "marginal_final_compress_s_vs_level15": ctime - baseline_time,
            "bytes_saved_vs_level15": archive_bytes - predicted_archive,
            "saved_bytes_per_marginal_final_second": (archive_bytes - predicted_archive) / max(ctime - baseline_time, 1e-9) if ctime > baseline_time else None,
        }

    # Pareto candidates in predicted size/final-compress-time space.
    pareto = []
    for variant, a in aggregate.items():
        dominated = any(
            b["predicted_archive_bytes"] <= a["predicted_archive_bytes"]
            and b["aggregate_final_compress_s"] <= a["aggregate_final_compress_s"]
            and (b["predicted_archive_bytes"] < a["predicted_archive_bytes"] or b["aggregate_final_compress_s"] < a["aggregate_final_compress_s"])
            for other, b in aggregate.items() if other != variant
        )
        if not dominated:
            pareto.append(variant)
    pareto.sort(key=lambda v: (aggregate[v]["predicted_archive_bytes"], aggregate[v]["aggregate_final_compress_s"]))

    return {
        "workload": name,
        "accepted_v029_bytes": accepted_v029,
        "canonical_user_tree_sha256": expected,
        "fixed_level15_archive_bytes": archive_bytes,
        "gap_to_v029_bytes": archive_bytes - accepted_v029,
        "filesystem_stage_s": stage_s,
        "scan_build_s": scan_s,
        "strong_verify_s": verify_s,
        "build_stats": build_stats,
        "final_call_hashes": len(measured),
        "aggregate": aggregate,
        "pareto_variants": pareto,
        "raw_records": measured,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_zstd_params_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_zstd_params_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    accepted = GENERAL._accepted_v029_rows()

    rows = []
    for name in TARGETS:
        target = int(accepted[("neutral_hostile_v1", name)]["accepted_v029_bytes"])
        row = _one(name, corpus / name, target, work)
        rows.append(row)
        ranked = sorted(row["aggregate"].items(), key=lambda kv: (kv[1]["gap_to_v029_bytes"], kv[1]["aggregate_final_compress_s"]))[:6]
        print(json.dumps({"workload": name, "baseline": row["fixed_level15_archive_bytes"], "target": target, "pareto": row["pareto_variants"], "best_size": ranked}, separators=(",", ":")), flush=True)

    # A parameter family is worth a whole-archive candidate only if at least one non-level19 hybrid
    # materially closes (>50%) the level15 byte gap on Analytics without paying >50% of level19's
    # measured final-compression time. This is deliberately an investigation gate, not release credit.
    analytics = next(r for r in rows if r["workload"] == "04_analytics_and_database")
    a0 = analytics["aggregate"]["level15"]
    a19 = analytics["aggregate"]["level19"]
    gap0 = max(1, int(a0["gap_to_v029_bytes"]))
    high_extra = max(1e-9, float(a19["aggregate_final_compress_s"]) - float(a0["aggregate_final_compress_s"]))
    promising = []
    for name, a in analytics["aggregate"].items():
        if name in ("level15", "level19"):
            continue
        recovered = int(a0["predicted_archive_bytes"]) - int(a["predicted_archive_bytes"])
        recovery_fraction = recovered / gap0
        extra_fraction = max(0.0, float(a["aggregate_final_compress_s"]) - float(a0["aggregate_final_compress_s"])) / high_extra
        if recovery_fraction >= 0.50 and extra_fraction <= 0.50:
            promising.append({"variant": name, "recovery_fraction": recovery_fraction, "level19_extra_time_fraction": extra_fraction, **a})
    promising.sort(key=lambda x: (-x["recovery_fraction"], x["level19_extra_time_fraction"]))
    return {
        "schema": "cmpct-v030-r4-zstd-parameter-decomposition-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "low_level": LOW_LEVEL,
        "high_level": HIGH_LEVEL,
        "probe_level": PROBE_LEVEL,
        "targets": list(TARGETS),
        "rows": rows,
        "analytics_promising_hybrids": promising,
        "hypothesis_supported": bool(promising),
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_selector_changed": False,
            "same_structural_representation": True,
            "ordinary_level_presets_reproduced_exactly": True,
            "mandatory_strong_verify": True,
            "canonical_filesystem_semantics_preserved": True,
        },
        "next_if_supported": "build and strong-verify the cheapest promising hybrid as a whole-archive R4 candidate, then test held-out hostile controls and exact product costs",
        "next_if_falsified": "retire zstd-parameter recombination as primary R4 and move to a representation change rather than another compression-level sweep",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zstd-param-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zstd-parameter-decomposition.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"supported": result["hypothesis_supported"], "analytics_promising_hybrids": result["analytics_promising_hybrids"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()

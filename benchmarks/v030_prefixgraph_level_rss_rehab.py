from __future__ import annotations

"""Frozen exact-owner PrefixGraph Zstd-level RSS rehabilitation sweep.

Diagnostic only. Direct payload compression, dictionary bytes, grammar and production source remain unchanged;
only the raw-prefix dictionary compressor used by `_prefix_codec` is varied over the preregistered levels.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_profile_isolation as ISO

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
LEVELS = (19, 18, 17, 16, 15)
ROUNDS = 3
PG = ISO.PG
EXPECTED_MODULE = "experiments._v030_canonical_prefixgraph"
EXPECTED_MAGIC = b"CMP25PG\0"


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def assert_owner() -> None:
    if PG.__name__ != EXPECTED_MODULE or PG.MAGIC != EXPECTED_MAGIC or ISO.RC.PG is not PG:
        raise RuntimeError("wrong canonical PrefixGraph owner")
    ISO.assert_research_modules_unchanged()


def codec_for_level(level: int):
    def codec(prefix: bytes):
        dictionary = PG.zstd.ZstdCompressionDict(prefix, dict_type=PG.zstd.DICT_TYPE_RAWCONTENT)
        compressor = PG.zstd.ZstdCompressor(level=level, dict_data=dictionary)
        return compressor, dictionary
    return codec


def build_worker(level: int, source: Path, archive: Path) -> dict:
    assert_owner()
    expected_tree = PG.treehash(source)
    original = PG._prefix_codec
    if level != PG.PAYLOAD_LEVEL:
        PG._prefix_codec = codec_for_level(level)
    baseline = rss_kib()
    started = time.perf_counter()
    try:
        stats = PG.build(source, archive)
    finally:
        PG._prefix_codec = original
    wall_s = time.perf_counter() - started
    peak = rss_kib()
    verify = PG.strong_verify(archive)
    if verify.get("ok") is not True or verify.get("tree_sha256") != expected_tree:
        raise RuntimeError("strong verification mismatch")
    blob = archive.read_bytes()
    return {
        "level": level,
        "owner_module": PG.__name__,
        "archive_bytes": len(blob),
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "tree_sha256": expected_tree,
        "selected_anchor": stats.get("anchor"),
        "anchor_auditions": stats.get("anchor_auditions"),
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        "wall_s": wall_s,
        "verification": verify,
    }


def child(level: int, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    done = subprocess.run(
        [sys.executable, __file__, "--worker-level", str(level), "--worker-source", str(source), "--worker-archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker {level} emitted no JSON")
    return json.loads(lines[-1])


def med(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    rows: dict[str, list[dict]] = {str(level): [] for level in LEVELS}

    # Rotate a fixed descending ladder so runner drift cannot systematically privilege one level.
    for round_index in range(ROUNDS):
        ordered = list(LEVELS[round_index:]) + list(LEVELS[:round_index])
        for level in ordered:
            archive = work_root / "archives" / f"round-{round_index}-level-{level}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            rows[str(level)].append(child(level, source, archive))

    deterministic = {}
    for level in LEVELS:
        ids = {
            (r["archive_bytes"], r["archive_sha256"], r["tree_sha256"], r["selected_anchor"], r["anchor_auditions"])
            for r in rows[str(level)]
        }
        deterministic[str(level)] = len(ids) == 1 and all(r["verification"].get("ok") is True for r in rows[str(level)])

    trees = {r["tree_sha256"] for rs in rows.values() for r in rs}
    owner_ok = all(r["owner_module"] == EXPECTED_MODULE for rs in rows.values() for r in rs)
    experiment_valid = len(trees) == 1 and owner_ok and all(deterministic.values())

    base_rows = rows["19"]
    base_peak = med(base_rows, "peak_rss_kib")
    base_wall = med(base_rows, "wall_s")
    base_bytes = int(base_rows[0]["archive_bytes"])
    metrics = {}
    qualified = []
    any_material_rss = False
    for level in LEVELS:
        rs = rows[str(level)]
        peak = med(rs, "peak_rss_kib")
        inc = med(rs, "incremental_peak_rss_kib")
        wall = med(rs, "wall_s")
        size = int(rs[0]["archive_bytes"])
        rss_reduction = 1.0 - peak / base_peak if base_peak else 0.0
        size_penalty = size - base_bytes
        size_penalty_ratio = size_penalty / base_bytes if base_bytes else float("inf")
        wall_ratio = wall / base_wall if base_wall else float("inf")
        qualifies = (
            level != 19 and experiment_valid and rss_reduction >= 0.15
            and size_penalty <= 8192 and size_penalty_ratio <= 0.005
            and wall_ratio <= 1.10
        )
        any_material_rss = any_material_rss or (level != 19 and rss_reduction >= 0.15)
        if qualifies:
            qualified.append(level)
        metrics[str(level)] = {
            "archive_bytes": size,
            "archive_sha256": rs[0]["archive_sha256"],
            "median_total_peak_rss_kib": peak,
            "median_incremental_peak_rss_kib": inc,
            "median_wall_s": wall,
            "rss_reduction_vs_19": rss_reduction,
            "size_penalty_bytes_vs_19": size_penalty,
            "size_penalty_ratio_vs_19": size_penalty_ratio,
            "wall_ratio_vs_19": wall_ratio,
            "deterministic": deterministic[str(level)],
            "qualified": qualifies,
        }

    if not experiment_valid:
        decision = "INVALID_CORRECTNESS_OR_DETERMINISM"
        selected = None
    elif qualified:
        decision = "PREFIXGRAPH_LEVEL_REHAB_SUPPORTED"
        selected = max(qualified)
    elif any_material_rss:
        decision = "PREFIXGRAPH_LEVEL_REHAB_TOO_EXPENSIVE"
        selected = None
    else:
        decision = "PREFIXGRAPH_LEVEL_REHAB_INSUFFICIENT"
        selected = None

    return {
        "schema": "cmpct-v030-prefixgraph-level-rss-rehab-v1",
        "source_commit": source_commit(),
        "target": list(TARGET),
        "levels": list(LEVELS),
        "rounds": ROUNDS,
        "rows": rows,
        "metrics": metrics,
        "gate": {"experiment_valid": experiment_valid, "tree_identity": len(trees) == 1, "owner_exact": owner_ok},
        "decision": decision,
        "selected_rehab_level": selected,
        "contract": {
            "minimum_total_peak_rss_reduction": 0.15,
            "maximum_size_penalty_bytes": 8192,
            "maximum_size_penalty_ratio": 0.005,
            "maximum_wall_ratio": 1.10,
            "direct_payload_level_changed": False,
            "dictionary_bytes_changed": False,
            "grammar_changed": False,
            "production_change": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker-level", type=int)
    p.add_argument("--worker-source", type=Path)
    p.add_argument("--worker-archive", type=Path)
    a = p.parse_args()
    if a.worker_level is not None:
        if a.worker_level not in LEVELS or a.worker_source is None or a.worker_archive is None:
            raise SystemExit("invalid worker arguments")
        print(json.dumps(build_worker(a.worker_level, a.worker_source, a.worker_archive), sort_keys=True))
        return
    if a.work_root is None or a.output is None:
        raise SystemExit("--work-root and --output required")
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "selected_rehab_level": result["selected_rehab_level"], "metrics": result["metrics"]}, indent=2))


if __name__ == "__main__":
    main()

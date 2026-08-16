from __future__ import annotations

"""Reproducible EntropyGraph-II benchmark runner.

The primary comparison is direct inherited v0.25 vs v0.28 on identical workload trees because that is
the causal release question. Mature competitors are also attempted when their executables are present;
unavailable tools are recorded rather than silently dropped from the schema.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _tree_stats(root: Path):
    files = [p for p in root.rglob("*") if p.is_file()]
    h = hashlib.sha256()
    for p in sorted(files):
        rel = p.relative_to(root).as_posix().encode()
        data = p.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    return len(files), sum(p.stat().st_size for p in files), h.hexdigest()


def _zip_deflate(root: Path, output: Path) -> dict:
    started = time.perf_counter()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(q for q in root.rglob("*") if q.is_file()):
            rel = p.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"available": True, "bytes": output.stat().st_size, "create_s": time.perf_counter() - started,
            "semantics": "standalone ZIP/Deflate-9; deterministic file bytes/timestamps; no CMPCT recovery layer"}


def _solid_tar_zstd(root: Path, output: Path) -> dict:
    zstd = shutil.which("zstd")
    if not zstd:
        return {"available": False, "reason": "zstd executable unavailable"}
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-tar-") as td:
        tar_path = Path(td) / "payload.tar"
        with tarfile.open(tar_path, "w") as tf:
            for p in sorted(q for q in root.rglob("*") if q.is_file()):
                info = tf.gettarinfo(str(p), arcname=p.relative_to(root).as_posix())
                info.mtime = 0; info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""
                with p.open("rb") as fh:
                    tf.addfile(info, fh)
        proc = subprocess.run([zstd, "-q", "-f", "-19", "-T1", str(tar_path), "-o", str(output)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240)
    if proc.returncode != 0:
        return {"available": False, "reason": proc.stderr.decode(errors="replace")[-500:]}
    return {"available": True, "bytes": output.stat().st_size, "create_s": time.perf_counter() - started,
            "semantics": "monolithic solid tar+Zstd-19 diagnostic; no random member access/recovery parity"}


def _optional_tool(name: str, root: Path, output: Path, command: list[str], semantics: str,
                   timeout: int = 300) -> dict:
    exe = shutil.which(name)
    if not exe:
        return {"available": False, "reason": f"{name} executable unavailable", "semantics": semantics}
    started = time.perf_counter()
    cmd = [exe if part == "{exe}" else part for part in command]
    try:
        proc = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": f"timeout after {timeout}s", "semantics": semantics}
    if proc.returncode != 0 or not output.exists():
        return {"available": False, "reason": proc.stderr.decode(errors="replace")[-500:], "semantics": semantics}
    return {"available": True, "bytes": output.stat().st_size, "create_s": time.perf_counter() - started,
            "semantics": semantics}


def _competitors(root: Path, temp: Path) -> dict:
    result = {
        "zip_deflate9": _zip_deflate(root, temp / "out.zip"),
        "tar_zstd19_solid": _solid_tar_zstd(root, temp / "out.tar.zst"),
    }
    result["seven_zip_lzma2"] = _optional_tool(
        "7z", root, temp / "out.7z",
        ["{exe}", "a", "-t7z", "-mx=9", "-mmt=1", str(temp / "out.7z"), "."],
        "7z/LZMA2 maximum-ish standalone archive; tool defaults otherwise recorded by environment",
    )
    result["zpaq_m5"] = _optional_tool(
        "zpaq", root, temp / "out.zpaq",
        ["{exe}", "a", str(temp / "out.zpaq"), ".", "-m5"],
        "ZPAQ method 5; high-ratio archival competitor with materially different speed/random-access semantics",
        600,
    )
    result["dwarfs"] = _optional_tool(
        "mkdwarfs", root, temp / "out.dwarfs",
        ["{exe}", "-i", ".", "-o", str(temp / "out.dwarfs"), "-l", "9"],
        "DwarFS read-only filesystem image; structural competitor, not ordinary mutable archive parity",
        600,
    )
    return result


def _run_suite(engine, root: Path, suite_name: str, with_competitors: bool) -> list[dict]:
    rows = []
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        files, logical, tree = _tree_stats(workload)
        with tempfile.TemporaryDirectory(prefix="cmpct-v028-row-") as td:
            temp = Path(td); archive = temp / "candidate.cmpct"
            stats = engine.bench(workload, archive)
            row = {
                "suite": suite_name, "name": workload.name, "files": files, "logical_bytes": logical,
                "tree_sha256": tree, "candidate_bytes": stats["archive_bytes"],
                "inherited_v025_bytes": stats["legacy_bytes"], "graph_bytes": stats["graph_bytes"],
                "selected": stats["selected"], "portfolio_create_s": stats["portfolio_create_s"],
                "strong_verify_median_s": stats["strong_verify_median_s"],
                "graph_stats": stats["graph"],
            }
            if with_competitors:
                row["competitors"] = _competitors(workload, temp)
            rows.append(row)
            print(json.dumps({"suite": suite_name, "name": workload.name, "candidate": row["candidate_bytes"],
                              "base": row["inherited_v025_bytes"], "selected": row["selected"]}), flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--suite", choices=("neutral", "hostile", "both"), default="both")
    ap.add_argument("--competitors", action="store_true")
    args = ap.parse_args()
    engine = _load(ROOT / "experiments" / "entropygraph_v028.py", "entropygraph_v028_bench_engine")
    rows = []
    with tempfile.TemporaryDirectory(prefix="cmpct-v028-corpora-") as td:
        temp = Path(td)
        if args.suite in ("neutral", "both"):
            neutral = _load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "neutral_v1")
            neutral_root = temp / "neutral"; neutral.build(neutral_root)
            rows += _run_suite(engine, neutral_root, "neutral_hostile_v1", args.competitors)
        if args.suite in ("hostile", "both"):
            hostile = _load(ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "resemblance_hostile_v1")
            hostile_root = temp / "hostile"; hostile.build(hostile_root)
            rows += _run_suite(engine, hostile_root, "resemblance_hostile_v1", args.competitors)
    base_total = sum(row["inherited_v025_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    graph_total = sum(row["graph_bytes"] for row in rows)
    record = {
        "schema": "cmpct-entropygraph-v028-benchmark-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "status": "experimental research engine; canonical revision 24 unchanged",
            "source": "experiments/entropygraph_v028.py",
            "format_magic": "CMPNX8 when resemblance graph wins; otherwise exact CMPNX5 fallback",
            "max_dependency_depth": 1,
            "max_decode_unit": 8 * 1024 * 1024,
        },
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(), "cpu_count": os.cpu_count(),
            "preflate_bridge": os.environ.get("CMPCT_PREFLATE_BRIDGE"),
            "tools": {name: shutil.which(name) for name in ("zstd", "7z", "zpaq", "mkdwarfs", "borg")},
        },
        "rows": rows,
        "totals": {
            "candidate_bytes": candidate_total, "inherited_v025_bytes": base_total, "raw_graph_bytes": graph_total,
            "smaller_than_v025_pct": (100.0 * (base_total - candidate_total) / base_total) if base_total else 0.0,
            "workloads_improved": sum(row["candidate_bytes"] < row["inherited_v025_bytes"] for row in rows),
            "workloads_regressed": sum(row["candidate_bytes"] > row["inherited_v025_bytes"] for row in rows),
            "resemblance_selected": sum(row["selected"] == "resemblance" for row in rows),
            "delta_nodes": sum(row["graph_stats"]["delta_nodes"] for row in rows),
            "preflate_wins": sum(row["graph_stats"]["preflate_wins"] for row in rows),
        },
        "contract": {
            "no_research_size_regression": "candidate must be <= inherited v0.25 per workload by exact artifact portfolio selection",
            "losses_retained": True,
            "competitor_semantic_mismatches_recorded": True,
            "note": "Portfolio selection intentionally exports extra create CPU; rows retain portfolio_create_s rather than hiding that cost.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["totals"], indent=2))
    if record["totals"]["workloads_regressed"]:
        raise SystemExit("research portfolio regressed archive size")


if __name__ == "__main__":
    main()

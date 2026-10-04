from __future__ import annotations

"""Attribute the frozen-v0.30 Genesis RSS signal to import/runtime versus build work.

Genesis used fresh processes, but the historical worker loaded the complete frozen product
surface before its timed operation and then reported process high-water RSS.  This diagnostic
keeps that exact source seal and records resident/high-water memory at process start, after
loading the frozen product, and after one build.  Workload generation happens in the parent;
each measured build runs in a fresh child so corpus-generator imports cannot contaminate RSS.

Research-only: no product, format, selector, benchmark threshold, or release policy changes.
"""

import argparse
import gc
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

FROZEN_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
FROZEN_MODULE = "experiments/entropygraph_v030_release_product.py"
GENESIS_REPORTED_RSS = 511_176_704


def _max_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _current_rss_bytes() -> int | None:
    try:
        pages = int(Path("/proc/self/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError):
        return None


def _snap(label: str) -> dict:
    return {
        "label": label,
        "current_rss_bytes": _current_rss_bytes(),
        "max_rss_bytes": _max_rss_bytes(),
    }


def _git_head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def _load_frozen_surface(checkout: Path):
    if _git_head(checkout) != FROZEN_SHA:
        raise RuntimeError("frozen v0.30 checkout SHA mismatch")
    module_path = checkout / FROZEN_MODULE
    for path in (checkout / "src", checkout / "experiments", checkout):
        sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location("cmpct_v030_rss_frozen_product", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v0.30 product")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    frozen_pkg = (checkout / "src" / "cmpct").resolve()
    loaded = {}
    for name, mod in sorted(sys.modules.items()):
        if name != "cmpct" and not name.startswith("cmpct."):
            continue
        raw = getattr(mod, "__file__", None)
        if not raw:
            continue
        path = Path(raw).resolve()
        try:
            path.relative_to(frozen_pkg)
        except ValueError as exc:
            raise RuntimeError(f"cmpct import escaped frozen checkout: {name}={path}") from exc
        loaded[name] = str(path)
    return module, loaded


def _child(checkout: Path, source: Path, archive: Path, output: Path) -> None:
    rows = [_snap("process_start")]
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    product, loaded = _load_frozen_surface(checkout)
    import_cpu = time.process_time() - cpu0; import_wall = time.perf_counter() - wall0
    gc.collect()
    rows.append(_snap("after_product_import"))
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    stats = product.build(source, archive)
    build_cpu = time.process_time() - cpu0; build_wall = time.perf_counter() - wall0
    rows.append(_snap("after_build"))
    if not archive.is_file():
        raise RuntimeError("frozen v0.30 build produced no archive")
    verified = product.strong_verify(archive)
    if isinstance(verified, dict) and verified.get("ok") is False:
        raise RuntimeError("frozen v0.30 strong verify failed")
    payload = {
        "source_sha": FROZEN_SHA,
        "snapshots": rows,
        "import_cpu_s": import_cpu,
        "import_wall_s": import_wall,
        "build_cpu_s": build_cpu,
        "build_wall_s": build_wall,
        "stored_bytes": archive.stat().st_size,
        "loaded_cmpct_modules": loaded,
        "product_stats": stats,
    }
    output.write_text(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _generate(repo: Path, work: Path) -> dict[str, Path]:
    neutral = _load(repo / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_rss_neutral")
    hostile = _load(repo / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_rss_hostile")
    repair = _load(repo / "benchmarks" / "neutral_hostile_determinism_repair_v6.py", "cmpct_rss_repair")
    repair.install_generation_hooks(neutral)
    nroot = work / "neutral"; hroot = work / "resemblance"
    neutral.build(nroot); repair.normalize_root(nroot); hostile.build(hroot)
    return {
        "analytics": nroot / "04_analytics_and_database",
        "deflate_family": hroot / "04_deflate_family",
    }


def run(repo: Path, checkout: Path, work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    sources = _generate(repo, work / "corpus")
    rows = []
    script = Path(__file__).resolve()
    for name, source in sources.items():
        rowdir = work / name; rowdir.mkdir()
        output = rowdir / "result.json"; archive = rowdir / "candidate.cmpct"
        subprocess.run([
            sys.executable, str(script), "--child", "--checkout", str(checkout),
            "--source", str(source), "--archive", str(archive), "--output", str(output),
        ], check=True, env=os.environ.copy())
        row = json.loads(output.read_text()); row["workload"] = name
        snaps = {s["label"]: s for s in row["snapshots"]}
        row["import_max_rss_delta_bytes"] = snaps["after_product_import"]["max_rss_bytes"] - snaps["process_start"]["max_rss_bytes"]
        row["build_incremental_max_rss_bytes"] = max(0, snaps["after_build"]["max_rss_bytes"] - snaps["after_product_import"]["max_rss_bytes"])
        row["import_floor_fraction_of_genesis_rss"] = snaps["after_product_import"]["max_rss_bytes"] / GENESIS_REPORTED_RSS
        rows.append(row)
    return {
        "schema": "cmpct-v030-genesis-rss-attribution-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "frozen_v030_sha": FROZEN_SHA,
        "genesis_reported_creation_rss_bytes": GENESIS_REPORTED_RSS,
        "rows": rows,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "frozen_source_sealed": True,
            "workload_generation_outside_measured_process": True,
            "product_format_selector_unchanged": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-rss-attribution-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-rss-attribution.json"))
    p.add_argument("--child", action="store_true")
    p.add_argument("--source", type=Path); p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.child:
        _child(a.checkout.resolve(), a.source.resolve(), a.archive.resolve(), a.output.resolve()); return
    result = run(a.repo.resolve(), a.checkout.resolve(), a.work_root.resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"rows": [{
        "workload": r["workload"], "stored_bytes": r["stored_bytes"],
        "snapshots": r["snapshots"], "import_floor_fraction_of_genesis_rss": r["import_floor_fraction_of_genesis_rss"],
        "build_incremental_max_rss_bytes": r["build_incremental_max_rss_bytes"],
        "import_cpu_s": r["import_cpu_s"], "build_cpu_s": r["build_cpu_s"],
    } for r in result["rows"]]}, indent=2))


if __name__ == "__main__":
    main()

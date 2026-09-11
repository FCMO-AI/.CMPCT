from __future__ import annotations

"""Same-runner source-sealed v0.29/v0.30 process-tree CPU diagnostic.

Genesis creation CPU used parent-only ``time.process_time()``. This diagnostic runs the frozen
v0.29 and frozen-v0.30 products on the same freshly generated source tree, same hosted runner and
same dependency environment, but charges self plus reaped-child CPU. It is diagnostic only and
cannot rewrite the original Genesis gate.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from benchmarks import v030_genesis_rss_attribution as RSS

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = RSS.FROZEN_SHA
MODULES = {
    "v029": "experiments/entropygraph_v029_residual_strict.py",
    "v030": "experiments/entropygraph_v030_release_product.py",
}
EXPECTED_HISTORICAL_TREES = {
    "analytics": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "deflate_family": "527a9e356e923e5bcc26566a8f677a7f7277af1577493e09c2bdca1b6d17154a",
}


def _historical_treehash(root: Path) -> str:
    import hashlib
    d = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        d.update(len(rel).to_bytes(4, "little")); d.update(rel)
        d.update(len(data).to_bytes(8, "little")); d.update(data)
    return d.hexdigest()


def _cpu() -> tuple[float, float]:
    me = resource.getrusage(resource.RUSAGE_SELF)
    ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime + me.ru_stime), float(ch.ru_utime + ch.ru_stime)


def _load_surface(checkout: Path, engine: str):
    expected = V029_SHA if engine == "v029" else V030_SHA
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if head != expected:
        raise RuntimeError(f"{engine} checkout mismatch {head} != {expected}")
    for path in (checkout / "src", checkout / "experiments", checkout):
        sys.path.insert(0, str(path))
    module_path = checkout / MODULES[engine]
    spec = importlib.util.spec_from_file_location(f"cmpct_tree_cpu_{engine}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    frozen_roots = ((checkout / "src" / "cmpct").resolve(), (checkout / "experiments").resolve())
    loaded = {}
    for name, mod in sorted(sys.modules.items()):
        if not (name == "cmpct" or name.startswith("cmpct.") or name == "experiments" or name.startswith("experiments.")):
            continue
        raw = getattr(mod, "__file__", None)
        if not raw:
            continue
        p = Path(raw).resolve()
        if not any(_under(p, root) for root in frozen_roots):
            raise RuntimeError(f"{engine} import escaped frozen checkout: {name}={p}")
        loaded[name] = str(p)
    return module, loaded


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root); return True
    except ValueError:
        return False


def _child(engine: str, checkout: Path, source: Path, archive: Path, output: Path) -> None:
    product, loaded = _load_surface(checkout, engine)
    self0, child0 = _cpu(); wall0 = time.perf_counter()
    stats = product.build(source, archive)
    wall = time.perf_counter() - wall0; self1, child1 = _cpu()
    if not archive.is_file(): raise RuntimeError("build produced no archive")
    verified = product.strong_verify(archive)
    if isinstance(verified, dict) and verified.get("ok") is False:
        raise RuntimeError("strong verify failed")
    self_cpu = self1 - self0; child_cpu = child1 - child0
    output.write_text(json.dumps({
        "engine": engine,
        "source_sha": V029_SHA if engine == "v029" else V030_SHA,
        "stored_bytes": archive.stat().st_size,
        "wall_s": wall,
        "self_cpu_s": self_cpu,
        "children_cpu_s": child_cpu,
        "tree_cpu_s": self_cpu + child_cpu,
        "loaded_modules": loaded,
        "stats": stats,
    }, sort_keys=True, default=str) + "\n")


def run(repo: Path, v029: Path, v030: Path, work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    sources = RSS._generate(repo, work / "corpus")
    rows = []
    script = Path(__file__).resolve()
    for workload, source in sources.items():
        historical = _historical_treehash(source)
        if historical != EXPECTED_HISTORICAL_TREES[workload]:
            raise RuntimeError(f"source drift {workload}: {historical}")
        results = {}
        for engine, checkout in (("v029", v029), ("v030", v030)):
            rowdir = work / workload / engine; rowdir.mkdir(parents=True, exist_ok=True)
            result = rowdir / "result.json"; archive = rowdir / "candidate.cmpct"
            subprocess.run([
                sys.executable, str(script), "--child", "--engine", engine,
                "--checkout", str(checkout), "--source", str(source),
                "--archive", str(archive), "--output", str(result),
            ], check=True, env=os.environ.copy())
            results[engine] = json.loads(result.read_text())
        a, b = results["v029"], results["v030"]
        rows.append({
            "workload": workload,
            "historical_tree_sha256": historical,
            "v029": a,
            "v030": b,
            "v030_over_v029_tree_cpu_ratio": b["tree_cpu_s"] / a["tree_cpu_s"],
            "v030_over_v029_wall_ratio": b["wall_s"] / a["wall_s"],
            "v030_minus_v029_bytes": b["stored_bytes"] - a["stored_bytes"],
        })
    return {
        "schema": "cmpct-v030-v029-process-tree-cpu-pair-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "v029_sha": V029_SHA,
        "v030_sha": V030_SHA,
        "rows": rows,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_runner": True,
            "same_source_tree": True,
            "same_dependency_environment": True,
            "fresh_process_per_engine_workload": True,
            "self_and_reaped_child_cpu_charged": True,
            "source_sealed_both_contenders": True,
            "original_genesis_gate_rewritten": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--v030-checkout", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-v029-tree-cpu-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-v029-tree-cpu.json"))
    p.add_argument("--child", action="store_true")
    p.add_argument("--engine", choices=("v029", "v030")); p.add_argument("--checkout", type=Path)
    p.add_argument("--source", type=Path); p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.child:
        _child(a.engine, a.checkout.resolve(), a.source.resolve(), a.archive.resolve(), a.output.resolve()); return
    d = run(a.repo.resolve(), a.v029_checkout.resolve(), a.v030_checkout.resolve(), a.work_root.resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps([{k:r[k] for k in ("workload","v030_over_v029_tree_cpu_ratio","v030_over_v029_wall_ratio","v030_minus_v029_bytes")} for r in d["rows"]], indent=2))


if __name__ == "__main__": main()

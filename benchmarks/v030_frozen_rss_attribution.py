from __future__ import annotations

"""Phase-attribution diagnostic for frozen-v0.30 hosted RSS.

Genesis reported process peak RSS after product operations.  ``ru_maxrss`` is monotonic and therefore
includes interpreter/import/harness state that predates the measured operation.  This diagnostic executes
the frozen v0.30 product in a fresh child, source-seals ``cmpct`` to the frozen checkout, and records Linux
current/high-water RSS at interpreter baseline, after product import, and after build.  It does not change
or score the frozen product.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

FROZEN_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
PRODUCT_MODULE = "experiments/entropygraph_v030_release_product.py"


def _proc_status() -> dict[str, int]:
    rows: dict[str, int] = {}
    status = Path("/proc/self/status")
    if status.is_file():
        for line in status.read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:")):
                key, raw = line.split(":", 1)
                value, unit = raw.strip().split()[:2]
                scale = 1024 if unit == "kB" else 1
                rows[key] = int(value) * scale
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rows["ru_maxrss_bytes"] = int(ru if sys.platform == "darwin" else ru * 1024)
    return rows


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _seal_cmpct(checkout: Path) -> dict[str, str]:
    root = (checkout / "src" / "cmpct").resolve()
    observed: dict[str, str] = {}
    for name, module in sorted(sys.modules.items()):
        if name != "cmpct" and not name.startswith("cmpct."):
            continue
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        p = Path(raw).resolve()
        observed[name] = str(p)
        if not _within(p, root):
            raise RuntimeError(f"cmpct import escaped frozen checkout: {name} -> {p}")
    return observed


def _load_frozen(checkout: Path):
    module_path = checkout / PRODUCT_MODULE
    for entry in (checkout / "src", checkout / "experiments", checkout):
        sys.path.insert(0, str(entry))
    spec = importlib.util.spec_from_file_location("cmpct_v030_rss_frozen_product", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v0.30 product")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, _seal_cmpct(checkout)


def _child(checkout: Path, root: Path, archive: Path) -> dict:
    checkout = checkout.resolve()
    actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if actual != FROZEN_SHA:
        raise RuntimeError(f"frozen checkout mismatch: {actual}")
    phases = {"interpreter_baseline": _proc_status()}
    product, imports = _load_frozen(checkout)
    phases["after_product_import"] = _proc_status()
    archive.parent.mkdir(parents=True, exist_ok=True)
    stats = product.build(root.resolve(), archive.resolve())
    phases["after_build"] = _proc_status()
    verified = product.strong_verify(archive.resolve())
    phases["after_strong_verify"] = _proc_status()
    return {
        "schema": "cmpct-v030-frozen-rss-attribution-child-v1",
        "frozen_sha": actual,
        "frozen_cmpct_import_roots": imports,
        "archive_bytes": archive.stat().st_size,
        "build_stats": stats,
        "strong_verify": verified,
        "phases": phases,
    }


def _run_parent(checkout: Path, root: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-rss-") as td:
        child_out = Path(td) / "child.json"
        archive = Path(td) / "candidate.cmpct"
        env = dict(os.environ)
        # Do not leak the current editable source tree into the child. Frozen checkout roots are installed
        # explicitly by the child before product import.
        env.pop("PYTHONPATH", None)
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--checkout", str(checkout),
            "--root", str(root),
            "--archive", str(archive),
            "--output", str(child_out),
        ]
        subprocess.run(cmd, check=True, env=env)
        row = json.loads(child_out.read_text())
    p = row["phases"]
    base = p["interpreter_baseline"].get("VmRSS", 0)
    imported = p["after_product_import"].get("VmRSS", 0)
    built_hwm = p["after_build"].get("VmHWM", p["after_build"].get("ru_maxrss_bytes", 0))
    import_hwm = p["after_product_import"].get("VmHWM", p["after_product_import"].get("ru_maxrss_bytes", 0))
    row["attribution"] = {
        "baseline_current_rss_bytes": base,
        "post_import_current_rss_bytes": imported,
        "import_current_increment_bytes": max(0, imported - base),
        "post_import_hwm_bytes": import_hwm,
        "post_build_hwm_bytes": built_hwm,
        "build_hwm_increment_over_import_bytes": max(0, built_hwm - import_hwm),
        "genesis_ru_maxrss_semantics": "process-lifetime high-water; includes pre-operation imports/runtime",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(row, indent=2, default=str) + "\n")
    print(json.dumps(row["attribution"], indent=2), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--archive", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--child", action="store_true")
    args = p.parse_args()
    if args.child:
        if args.archive is None:
            raise SystemExit("--archive required in child mode")
        result = _child(args.checkout, args.root, args.archive)
        args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    else:
        _run_parent(args.checkout, args.root, args.output)


if __name__ == "__main__":
    main()

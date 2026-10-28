from __future__ import annotations

"""Fresh-process worker for same-input frozen-v0.29 comparisons.

This is intentionally small and stdlib-only before the historical product surface is
loaded.  The whole v0.29 checkout is frozen, not merely the experiment facade: every
loaded ``cmpct`` module must resolve below that checkout's ``src/cmpct`` directory or
the worker fails closed.  This preserves the source-seal law established by the ONE
Genesis diagnosis while allowing post-Genesis v0.30 referees to compare new candidates
against the exact mature v0.29 source package on one caller-owned input tree.
"""

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

SCHEMA = "cmpct-v030-r4-frozen-v029-product-worker-v1"
V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
PRODUCT_MODULE = "experiments/entropygraph_v029_residual_strict.py"


def _git_head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _assert_frozen_imports(checkout: Path) -> dict[str, str]:
    frozen_pkg = (checkout / "src" / "cmpct").resolve()
    if not frozen_pkg.is_dir():
        raise RuntimeError(f"frozen cmpct package missing: {frozen_pkg}")
    observed: dict[str, str] = {}
    escaped: dict[str, str] = {}
    for name, module in sorted(sys.modules.items()):
        if name != "cmpct" and not name.startswith("cmpct."):
            continue
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        path = Path(raw).resolve()
        observed[name] = str(path)
        if not _is_within(path, frozen_pkg):
            escaped[name] = str(path)
    if escaped:
        raise RuntimeError(
            "historical contender imported cmpct outside frozen checkout: "
            + json.dumps(escaped, sort_keys=True)
        )
    return observed


def _load(checkout: Path):
    checkout = checkout.resolve()
    actual = _git_head(checkout)
    if actual != V029_SHA:
        raise RuntimeError(f"v0.29 checkout SHA mismatch: expected {V029_SHA}, got {actual}")
    module_path = checkout / PRODUCT_MODULE
    if not module_path.is_file():
        raise RuntimeError(f"frozen v0.29 product module missing: {module_path}")
    for path in (checkout / "src", checkout / "experiments", checkout):
        sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location("cmpct_v030_frozen_v029", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v0.29 surface")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    roots = _assert_frozen_imports(checkout)
    return module, roots


def _regular_file_digests(root: Path) -> dict[str, tuple[int, str]]:
    rows: dict[str, tuple[int, str]] = {}
    for p in root.rglob("*"):
        st = p.lstat()
        if stat.S_ISREG(st.st_mode):
            data = p.read_bytes()
            rows[p.relative_to(root).as_posix()] = (len(data), sha256(data).hexdigest())
    return dict(sorted(rows.items()))


def _verify_result_ok(value: Any) -> bool:
    if isinstance(value, dict) and "ok" in value:
        return bool(value["ok"])
    return value is None or value is True or isinstance(value, dict)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    checkout = a.checkout.resolve()
    source = a.source.resolve()
    archive = a.archive.resolve()
    if not source.is_dir():
        raise RuntimeError("source is not a directory")
    surface, roots = _load(checkout)
    source_files = _regular_file_digests(source)

    archive.parent.mkdir(parents=True, exist_ok=True)
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    stats = surface.build(source, archive)
    create_cpu = time.process_time() - cpu0
    create_wall = time.perf_counter() - wall0
    if not archive.is_file():
        raise RuntimeError("frozen v0.29 did not emit an archive")
    archive_bytes = archive.read_bytes()

    verify = surface.strong_verify(archive)
    if not _verify_result_ok(verify):
        raise RuntimeError(f"frozen v0.29 strong_verify failed: {verify!r}")
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-v029-extract-") as td:
        dst = Path(td) / "tree"
        dst.mkdir()
        surface.extract(archive, dst)
        extracted = _regular_file_digests(dst)
    if extracted != source_files:
        missing = sorted(set(source_files) - set(extracted))
        extra = sorted(set(extracted) - set(source_files))
        changed = sorted(
            rel for rel in set(source_files) & set(extracted) if source_files[rel] != extracted[rel]
        )
        raise RuntimeError(
            f"frozen v0.29 reconstruction mismatch missing={missing[:5]} extra={extra[:5]} changed={changed[:5]}"
        )

    roots_after = _assert_frozen_imports(checkout)
    if roots_after != roots:
        # Additional frozen modules are allowed to load during build, but none may escape.
        roots = roots_after
    result = {
        "schema": SCHEMA,
        "frozen_source_sha": V029_SHA,
        "frozen_product_module": PRODUCT_MODULE,
        "frozen_cmpct_import_roots": roots,
        "source_regular_files": len(source_files),
        "source_regular_bytes": sum(n for n, _ in source_files.values()),
        "stored_bytes": len(archive_bytes),
        "archive_sha256": sha256(archive_bytes).hexdigest(),
        "create_cpu_s": create_cpu,
        "create_wall_s": create_wall,
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)),
        "strong_verify": repr(verify),
        "reconstruction_exact": True,
        "product_stats": repr(stats),
        "source_sealed": True,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "frozen_source_sha", "stored_bytes", "create_cpu_s", "create_wall_s",
        "peak_rss_bytes", "reconstruction_exact", "source_sealed"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()

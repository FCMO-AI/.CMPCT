"""Attempt-5 portfolio optimization: reject an expensive single-file mosaic dead end.

The accepted attempt-5 compiler remains in `entropygraph_v029_residual_pack.py`. This wrapper changes
only *portfolio scheduling*: it first builds the exact v0.28 baseline, then skips the multi-root
Placement Compiler when the input has one logical file **and** v0.28 already selected its inherited
v0.25 fallback. In that state there are no independent logical source files for Mosaic's mission, and
the first generalization run measured a 22.8x creation-cost outlier constructing a graph that was thrown
away unchanged.

All multi-file inputs—including every fixed mosaic v1/v2 workload and both inherited-frontier winners—
still execute the accepted attempt-5 engine byte-for-byte. Canonical format revision 24 remains
unchanged; this is research portfolio policy only.

Footnote: the reject is intentionally conjunctive. A single-file tree whose v0.28 graph actually wins is
*not* skipped, because residual packing may still improve real graph deltas. This keeps the optimization
narrower than a blanket "mosaic only works across files" rule.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "entropygraph_v029_residual_pack.py"


def _load_base():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_residual_attempt5_accepted", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load accepted attempt-5 engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
P = BASE.P
A4 = BASE.A4
V028 = BASE.V028
MAG = BASE.MAG
TAIL = BASE.TAIL
HDR = BASE.HDR
FTR = BASE.FTR
PH = BASE.PH
MAX_READ_AMP = BASE.MAX_READ_AMP
MAX_RESIDUAL_PACK = BASE.MAX_RESIDUAL_PACK
MAX_ADDITIONAL_RECIPE_AMP = BASE.MAX_ADDITIONAL_RECIPE_AMP
# Footnote: hostile metadata tests intentionally reach through the strict wrapper to low-level grammar
# primitives. Keep the common names explicit for readability, then delegate every other unknown module
# attribute to the accepted attempt-5 engine via ``__getattr__`` below. The optimization is therefore a
# transparent scheduling decorator rather than a forked/narrowed grammar API.
H = BASE.H
zc = BASE.zc
zd = BASE.zd
MAX_DECODE_UNIT = BASE.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = BASE.MAX_DECODER_MEMORY


def __getattr__(name: str):
    """Delegate unmodified grammar/runtime attributes to the accepted attempt-5 engine.

    Footnote: Python calls module-level ``__getattr__`` only after ordinary lookup fails, so the handful
    of scheduling functions defined below still override the parent while parser constants, codecs,
    hashes, Merkle helpers and future hostile-test hooks remain exactly those of the preserved engine.
    """
    return getattr(BASE, name)


def _logical_file_count(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file())


def _fast_reject(v028_stats: dict, logical_files: int) -> str | None:
    if logical_files == 1 and v028_stats.get("selected") == "entropygraph-v025-fallback":
        return "single-file-and-v028-inherited-fallback"
    return None


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-residual-portfolio-fast-") as td:
        temp = Path(td)
        v028_path = temp / "v028.cmpct"
        graph_path = temp / "candidate.cmpct"
        v028_stats = V028.build(root, v028_path)
        logical_files = _logical_file_count(root)
        reject = _fast_reject(v028_stats, logical_files)
        if reject is not None:
            shutil.copyfile(v028_path, out)
            # Footnote: return the same statistics surface used by the generalization harness. Zero
            # research nodes is evidence that the expensive candidate was not evaluated, not a claim
            # that the inherited archive magically gained new semantics.
            graph_stats = {
                "create_s": 0.0,
                "graph_bytes": v028_path.stat().st_size,
                "mosaic_nodes": 0,
                "residual_pack_records": 0,
                "residual_packed_delta_nodes": 0,
                "max_mosaic_read_amplification": 0.0,
                "max_additional_recipe_read_amplification": 0.0,
                "fast_reject_reason": reject,
                "fast_reject_logical_files": logical_files,
            }
            return {
                "selected": "v028-fallback",
                "archive_bytes": out.stat().st_size,
                "v028_bytes": v028_path.stat().st_size,
                "mosaic_graph_bytes": v028_path.stat().st_size,
                "smaller_than_v028_pct": 0.0,
                "portfolio_create_s": time.perf_counter() - started,
                "v028": v028_stats,
                "mosaic": graph_stats,
                "fast_reject_reason": reject,
            }

        graph_stats = BASE._build_graph(root, graph_path)
        if graph_path.stat().st_size < v028_path.stat().st_size:
            shutil.copyfile(graph_path, out)
            selected = "mosaic"
        else:
            shutil.copyfile(v028_path, out)
            selected = "v028-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v028_bytes": v028_path.stat().st_size,
            "mosaic_graph_bytes": graph_path.stat().st_size,
            "smaller_than_v028_pct": (
                (v028_path.stat().st_size - out.stat().st_size) / max(1, v028_path.stat().st_size) * 100.0
            ),
            "portfolio_create_s": time.perf_counter() - started,
            "v028": v028_stats,
            "mosaic": graph_stats,
            "fast_reject_reason": None,
        }


def build_graph(root: Path, out: Path) -> dict:
    # Raw graph callers explicitly asked for the research graph and therefore bypass portfolio policy.
    return BASE.build_graph(root, out)


def extract(archive: Path, dst: Path) -> None:
    BASE.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return BASE.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    import statistics
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = BASE.treehash(root)
    return result


def _open(path: Path):
    return BASE._open(path)

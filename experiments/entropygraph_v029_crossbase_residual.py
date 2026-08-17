"""CMPCT v0.29 research attempt #7 — Cross-Base Residual Program Packing.

Attempt #5 physically packs small one-base delta programs only when they share the same direct base.
That restriction is not part of CMPNX11's reader grammar: every ``delta_pack`` descriptor already stores
its own ``base_id``, residual record id, slice offset and slice length.  The reader authenticates the whole
physical record, slices the target recipe, then decodes that slice against the descriptor's own direct
base.  Attempt #7 therefore tests whether recipes from *different* bases can share one physical record
without changing dependency depth, reader code, recovery semantics or the <=2x recipe-overread policy.

Footnote: the accepted attempt-5 archive is always built independently and remains the exact final
fallback.  This experiment monkey-patches only attempt #5's encoder-side plan chooser while building the
experimental graph; the unchanged attempt-5 reader must strong-verify any selected result.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
PACK_PATH = HERE / "entropygraph_v029_residual_pack.py"
STRICT_PATH = HERE / "entropygraph_v029_residual_strict.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PACK = _load(PACK_PATH, "cmpct_v029_crossbase_pack_source")
A5 = _load(STRICT_PATH, "cmpct_v029_crossbase_attempt5")
BASE = A5.BASE

ORDERINGS = ("target", "recipe-prefix")
_ORIGINAL_CHOOSE_PLAN = PACK._choose_plan
_LAST_PLAN_DIAG: dict = {}


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _ordered(programs: list[dict], strategy: str) -> list[dict]:
    if strategy == "target":
        return sorted(programs, key=lambda row: (row["target_id"], row["base_id"]))
    if strategy == "recipe-prefix":
        # Footnote: this is intentionally a cheap physical-similarity hint, not a learned or
        # benchmark-specific classifier.  The first 32 recipe bytes are already present and often expose
        # common opcode/address structure; target/base ids provide a stable total order for ties.
        return sorted(
            programs,
            key=lambda row: (row["raw_delta"][:32], row["raw_delta_bytes"], row["target_id"], row["base_id"]),
        )
    raise RuntimeError(f"unknown cross-base residual ordering: {strategy}")


def _plan_crossbase(programs: list[dict], limit: int, strategy: str) -> dict:
    groups = []
    current: list[dict] = []
    current_raw = 0
    for row in _ordered(programs, strategy):
        candidate_raw = current_raw + row["raw_delta_bytes"]
        candidate = current + [row]
        candidate_amp = max(candidate_raw / max(1, member["target_len"]) for member in candidate)
        if current and (candidate_raw > limit or candidate_amp > PACK.MAX_ADDITIONAL_RECIPE_AMP):
            groups.append(PACK._pack_group(current))
            current = [row]
            current_raw = row["raw_delta_bytes"]
        else:
            current = candidate
            current_raw = candidate_raw
    if current:
        groups.append(PACK._pack_group(current))

    eligible = [
        group for group in groups
        if len(group["programs"]) >= 2
        and len(group["raw"]) <= PACK.MAX_RESIDUAL_PACK
        and group["max_amp"] <= PACK.MAX_ADDITIONAL_RECIPE_AMP
        and group["net"] >= PACK.MIN_RESIDUAL_NET_SAVING
    ]
    return {
        "strategy": strategy,
        "limit": limit,
        "groups": groups,
        "eligible": eligible,
        "net": sum(group["net"] for group in eligible),
        "max_amp": max((group["max_amp"] for group in eligible), default=0.0),
        "mixed_base_groups": sum(len({row["base_id"] for row in group["programs"]}) > 1 for group in eligible),
        "mixed_base_members": sum(
            len(group["programs"])
            for group in eligible
            if len({row["base_id"] for row in group["programs"]}) > 1
        ),
    }


def _choose_plan_crossbase(programs: list[dict]) -> dict:
    """Tournament attempt #5's exact planner against two bounded cross-base orderings."""
    global _LAST_PLAN_DIAG
    baseline = _ORIGINAL_CHOOSE_PLAN(programs)
    best = baseline
    selected_crossbase = False
    for strategy in ORDERINGS:
        for kib in PACK.RESIDUAL_LIMITS:
            candidate = _plan_crossbase(programs, kib * 1024, strategy)
            # Footnote: attempt #5 wins *all* estimated-byte ties.  Lower read amplification alone does
            # not justify physical-layout churn in a size experiment; a cross-base plan must buy real
            # estimated bytes before the exact archive tournament is allowed to consider it.
            if candidate["net"] > best["net"]:
                best = candidate
                selected_crossbase = True

    if selected_crossbase:
        _LAST_PLAN_DIAG = {
            "selected_crossbase_plan": True,
            "strategy": best["strategy"],
            "limit": int(best["limit"]),
            "estimated_net_saving": int(best["net"]),
            "max_amp": float(best["max_amp"]),
            "mixed_base_groups": int(best["mixed_base_groups"]),
            "mixed_base_members": int(best["mixed_base_members"]),
            "eligible_groups": len(best["eligible"]),
        }
    else:
        _LAST_PLAN_DIAG = {
            "selected_crossbase_plan": False,
            "strategy": "attempt5-same-base-fallback",
            "limit": int(baseline["limit"]),
            "estimated_net_saving": int(baseline["net"]),
            "max_amp": float(baseline["max_amp"]),
            "mixed_base_groups": 0,
            "mixed_base_members": 0,
            "eligible_groups": len(baseline["eligible"]),
        }
    return best


def _build_crossbase_graph(root: Path, out: Path) -> dict:
    global _LAST_PLAN_DIAG
    previous = PACK._choose_plan
    _LAST_PLAN_DIAG = {}
    PACK._choose_plan = _choose_plan_crossbase
    try:
        stats = PACK._build_graph(root, out)
    finally:
        PACK._choose_plan = previous
    stats["crossbase_residual_plan"] = dict(_LAST_PLAN_DIAG)
    return stats


def build_graph(root: Path, out: Path) -> dict:
    return _build_crossbase_graph(root, out)


def build(root: Path, out: Path) -> dict:
    """Final exact-byte tournament against the accepted attempt-5 scheduler/artifact."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-crossbase-residual-") as td:
        temp = Path(td)
        attempt5_path = temp / "attempt5.cmpct"
        crossbase_path = temp / "crossbase.cmpct"
        attempt5_stats = A5.build(root, attempt5_path)
        cross_stats = _build_crossbase_graph(root, crossbase_path)
        if crossbase_path.stat().st_size < attempt5_path.stat().st_size:
            shutil.copyfile(crossbase_path, out)
            selected = "crossbase-residual"
            selected_stats = cross_stats
        else:
            shutil.copyfile(attempt5_path, out)
            selected = attempt5_stats["selected"]
            selected_stats = attempt5_stats["mosaic"]
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "attempt5_bytes": attempt5_path.stat().st_size,
            "v028_bytes": int(attempt5_stats["v028_bytes"]),
            "crossbase_graph_bytes": crossbase_path.stat().st_size,
            "saving_vs_attempt5_bytes": attempt5_path.stat().st_size - out.stat().st_size,
            "portfolio_create_s": time.perf_counter() - started,
            "attempt5_selected": attempt5_stats["selected"],
            "mosaic": selected_stats,
            "crossbase_graph_stats": cross_stats,
            "crossbase_residual_plan": cross_stats.get("crossbase_residual_plan", {}),
        }


def extract(archive: Path, dst: Path) -> None:
    A5.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return A5.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter()
        strong_verify(out)
        samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.29 cross-base residual research engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()

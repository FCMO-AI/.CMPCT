"""CMPCT v0.29 research attempt #6 — Locality Budget Compiler.

Attempt #5 chooses one global direct-root pack ceiling per workload from 64 KiB through 2 MiB. That is
simple, but it spends locality budget uniformly: one region cannot remain in small selective-read packs
while another region spends otherwise unused read budget on a larger context that compresses better.

This experiment changes only encoder-side physical partitioning. It preserves attempt #5's exact graph
grammar, depth-1 dependencies, residual-program format, integrity/recovery semantics and 2 MiB physical
pack ceiling. The accepted attempt-5 archive is built first and remains an exact byte-for-byte fallback.

Footnote: this file deliberately imports the accepted attempt-5 implementation instead of copying it.
The only monkey-patched seam is v0.28's `_choose_pack_plan`, and that patch exists only while constructing
the experimental graph. Reader code is not patched, so a selected result must verify with the unchanged
attempt-5 reader before it can count as evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
A5_PATH = HERE / "entropygraph_v029_residual_strict.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A5 = _load(A5_PATH, "cmpct_entropygraph_v029_pack_budget_attempt5")
FAST = A5.IMPL
RAW_A5 = FAST.BASE
V028 = FAST.V028
BASE = A5.BASE

MAX_READ_AMP = 8.0
MAX_PACK_BYTES = 2 * 1024 * 1024
BASE_LIMITS = (64, 128, 256, 512, 1024, 2048)  # KiB; same audition envelope as v0.28.
MAX_BASE_GROUPS = 512
MAX_MERGED_BASE_GROUPS = 64
MAX_PARETO_STATES = 4096

_ORIGINAL_CHOOSE = V028._choose_pack_plan
_ORIGINAL_PACK_PLAN = V028._pack_plan


@dataclass(frozen=True)
class _State:
    decoded: int
    cost: int
    worst_member_amp: float
    previous: "_State | None"
    group: tuple[int, ...]


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _record_cost(raw: bytes) -> int:
    _, payload = V028._compress_record(raw)
    return V028.PH.size + len(payload)


def _group_raw_bytes(group: list[int] | tuple[int, ...], nodes: list[bytes]) -> int:
    return sum(len(nodes[node_id]) for node_id in group)


def _worst_member_amp(groups: list[list[int]] | list[tuple[int, ...]], nodes: list[bytes]) -> float:
    worst = 0.0
    for group in groups:
        raw_bytes = _group_raw_bytes(group, nodes)
        for node_id in group:
            worst = max(worst, raw_bytes / max(1, len(nodes[node_id])))
    return worst


def _prune_pareto(states: list[_State]) -> list[_State] | None:
    """Keep only states for which neither read cost nor stored bytes is jointly worse.

    Footnote: exceeding the hard state cap rejects this source plan instead of approximating it. A
    benchmark optimizer must not silently drop inconvenient states and then describe the result as an
    exact byte optimum. Other source limits and the unchanged attempt-5 fallback remain available.
    """
    states.sort(key=lambda row: (row.decoded, row.cost, row.worst_member_amp))
    kept: list[_State] = []
    best_cost = None
    for row in states:
        if best_cost is None or row.cost < best_cost:
            kept.append(row)
            best_cost = row.cost
    if len(kept) > MAX_PARETO_STATES:
        return None
    return kept


def _coarsen_source_plan(nodes: list[bytes], root_ids: list[int], base_groups: list[list[int]],
                         source_limit: int, original_worst: float) -> tuple[tuple[int, float, int, list[list[int]]] | None, dict]:
    """Find a lower-byte contiguous coarsening under the inherited weighted read budget.

    The search never reorders roots: v0.28's similarity order is the semantic starting point. It only
    decides which adjacent existing groups should share one physical record. This makes the current
    global plan a reachable no-op state while allowing different regions to spend different amounts of
    locality budget.
    """
    if not base_groups or len(base_groups) > MAX_BASE_GROUPS:
        return None, {"source_limit": source_limit, "skipped": "base-group-cap", "base_groups": len(base_groups)}

    logical = sum(max(1, len(nodes[node_id])) for node_id in root_ids)
    max_decoded = int(MAX_READ_AMP * logical)
    source_worst = _worst_member_amp(base_groups, nodes)
    allowed_worst = max(MAX_READ_AMP, original_worst)
    n = len(base_groups)
    frontiers: list[list[_State]] = [[] for _ in range(n + 1)]
    frontiers[0] = [_State(0, 0, 0.0, None, ())]
    interval_cache: dict[tuple[int, int], tuple[tuple[int, ...], int, int, float]] = {}

    def interval(start: int, end: int):
        key = (start, end)
        cached = interval_cache.get(key)
        if cached is not None:
            return cached
        ids = tuple(node_id for group in base_groups[start:end] for node_id in group)
        raw_bytes = _group_raw_bytes(ids, nodes)
        if raw_bytes > MAX_PACK_BYTES:
            interval_cache[key] = (ids, raw_bytes, -1, float("inf"))
            return interval_cache[key]
        raw = b"".join(nodes[node_id] for node_id in ids)
        cost = _record_cost(raw)
        worst = max((raw_bytes / max(1, len(nodes[node_id])) for node_id in ids), default=0.0)
        interval_cache[key] = (ids, raw_bytes, cost, worst)
        return interval_cache[key]

    for end in range(1, n + 1):
        candidates: list[_State] = []
        lower = max(0, end - MAX_MERGED_BASE_GROUPS)
        for start in range(end - 1, lower - 1, -1):
            ids, raw_bytes, segment_cost, segment_worst = interval(start, end)
            if raw_bytes > MAX_PACK_BYTES:
                break
            if segment_worst > allowed_worst + 1e-12:
                continue
            segment_decoded = raw_bytes * len(ids)
            for previous in frontiers[start]:
                decoded = previous.decoded + segment_decoded
                if decoded > max_decoded:
                    continue
                candidates.append(_State(
                    decoded=decoded,
                    cost=previous.cost + segment_cost,
                    worst_member_amp=max(previous.worst_member_amp, segment_worst),
                    previous=previous,
                    group=ids,
                ))
        pruned = _prune_pareto(candidates)
        if pruned is None:
            return None, {
                "source_limit": source_limit,
                "skipped": "pareto-state-cap",
                "position": end,
                "base_groups": n,
            }
        if not pruned:
            return None, {"source_limit": source_limit, "skipped": "no-feasible-partition", "position": end}
        frontiers[end] = pruned

    best = min(frontiers[n], key=lambda row: (row.cost, row.decoded, row.worst_member_amp))
    groups: list[list[int]] = []
    cursor: _State | None = best
    while cursor is not None and cursor.previous is not None:
        groups.append(list(cursor.group))
        cursor = cursor.previous
    groups.reverse()
    if sorted(node_id for group in groups for node_id in group) != sorted(root_ids):
        raise RuntimeError("locality-budget partition lost or duplicated a root")

    max_group = max((_group_raw_bytes(group, nodes) for group in groups), default=0)
    amp = best.decoded / max(1, logical)
    return (best.cost, amp, max_group, groups), {
        "source_limit": source_limit,
        "source_worst_member_amp": source_worst,
        "bytes": best.cost,
        "read_amp": amp,
        "worst_member_amp": best.worst_member_amp,
        "groups": len(groups),
        "max_group_bytes": max_group,
        "skipped": None,
    }


def _choose_pack_plan_budgeted(nodes: list[bytes], sketches, root_ids: list[int]):
    """Strictly dominate the current global-ceiling audition when the exact bytes permit it."""
    original, original_trials = _ORIGINAL_CHOOSE(nodes, sketches, root_ids)
    original_cost, original_amp, original_limit, original_groups = original
    original_worst = _worst_member_amp(original_groups, nodes)
    best = original
    best_diag = {
        "source_limit": original_limit,
        "bytes": original_cost,
        "read_amp": original_amp,
        "worst_member_amp": original_worst,
        "groups": len(original_groups),
        "max_group_bytes": max((_group_raw_bytes(group, nodes) for group in original_groups), default=0),
        "saving_vs_global": 0,
        "selected": False,
        "strategy": "global-limit-fallback",
    }
    diagnostics = []

    for limit_kib in BASE_LIMITS:
        source_limit = limit_kib * 1024
        source_cost, source_amp, source_groups = _ORIGINAL_PACK_PLAN(nodes, sketches, root_ids, source_limit)
        if source_amp > MAX_READ_AMP:
            diagnostics.append({
                "strategy": "read-budget-partition",
                "source_limit": source_limit,
                "skipped": "source-plan-over-weighted-budget",
                "source_read_amp": source_amp,
            })
            continue
        candidate, diag = _coarsen_source_plan(
            nodes, root_ids, [list(group) for group in source_groups], source_limit, original_worst
        )
        diag["strategy"] = "read-budget-partition"
        diagnostics.append(diag)
        if candidate is None:
            continue
        cost, amp, max_group, groups = candidate
        worst = float(diag["worst_member_amp"])
        # Footnote: ties stay with the historical plan. Spending locality or changing physical boundaries
        # for zero byte gain would create churn with no user-visible benefit.
        if cost < best[0] and amp <= MAX_READ_AMP and worst <= max(MAX_READ_AMP, original_worst) + 1e-12:
            best = (cost, amp, max_group, groups)
            best_diag = dict(diag)
            best_diag.update({
                "saving_vs_global": original_cost - cost,
                "selected": True,
                "strategy": "read-budget-partition",
            })

    trials = [dict(row, strategy="global-limit") for row in original_trials]
    for row in diagnostics:
        trial = dict(row)
        trial["selected"] = bool(
            best_diag.get("selected")
            and row.get("source_limit") == best_diag.get("source_limit")
            and row.get("bytes") == best_diag.get("bytes")
        )
        trials.append(trial)
    trials.append(dict(best_diag, strategy="pack-budget-summary"))
    return best, trials


def _build_budget_graph(root: Path, out: Path) -> dict:
    """Build one attempt-5 graph with only the pack selector replaced, then restore global state."""
    previous = V028._choose_pack_plan
    V028._choose_pack_plan = _choose_pack_plan_budgeted
    try:
        stats = RAW_A5._build_graph(root, out)
    finally:
        V028._choose_pack_plan = previous

    summary = None
    for row in stats.get("pack_trials", []):
        if row.get("strategy") == "pack-budget-summary":
            summary = row
            break
    stats["pack_budget"] = summary or {
        "strategy": "pack-budget-summary",
        "selected": False,
        "saving_vs_global": 0,
    }
    return stats


def build_graph(root: Path, out: Path) -> dict:
    return _build_budget_graph(root, out)


def build(root: Path, out: Path) -> dict:
    """Tournament the new graph against the already accepted attempt-5 archive, never just v0.28."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-budget-portfolio-") as td:
        temp = Path(td)
        attempt5_path = temp / "attempt5.cmpct"
        budget_path = temp / "pack-budget.cmpct"

        attempt5_stats = A5.build(root, attempt5_path)
        budget_started = time.perf_counter()
        budget_stats = _build_budget_graph(root, budget_path)
        budget_create_s = time.perf_counter() - budget_started

        if budget_path.stat().st_size < attempt5_path.stat().st_size:
            shutil.copyfile(budget_path, out)
            selected = "mosaic"
            selected_stats = budget_stats
            pack_budget_selected = True
            fast_reject_reason = None
        else:
            shutil.copyfile(attempt5_path, out)
            selected = attempt5_stats["selected"]
            selected_stats = attempt5_stats["mosaic"]
            pack_budget_selected = False
            fast_reject_reason = attempt5_stats.get("fast_reject_reason")

        v028_bytes = int(attempt5_stats["v028_bytes"])
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v028_bytes": v028_bytes,
            "mosaic_graph_bytes": budget_path.stat().st_size,
            "smaller_than_v028_pct": (
                (v028_bytes - out.stat().st_size) / max(1, v028_bytes) * 100.0
            ),
            "portfolio_create_s": time.perf_counter() - started,
            "v028": attempt5_stats["v028"],
            "mosaic": selected_stats,
            "fast_reject_reason": fast_reject_reason,
            "attempt5_bytes": attempt5_path.stat().st_size,
            "attempt5_selected": attempt5_stats["selected"],
            "pack_budget_graph_bytes": budget_path.stat().st_size,
            "pack_budget_selected": pack_budget_selected,
            "saving_vs_attempt5_bytes": attempt5_path.stat().st_size - out.stat().st_size,
            "pack_budget_graph_create_s": budget_create_s,
            "pack_budget_graph_stats": budget_stats,
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
    parser = argparse.ArgumentParser(description="CMPCT v0.29 Locality Budget Compiler research engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination)
        print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()

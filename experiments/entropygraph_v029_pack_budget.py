"""CMPCT v0.29 research attempt #6 — Locality Budget Compiler.

Attempt #5 chooses one global direct-root pack ceiling per workload from 64 KiB through 2 MiB. That is
simple, but it spends locality budget uniformly: one region cannot remain in small selective-read packs
while another region spends otherwise unused read budget on a larger context that compresses better.

Attempt #6 replaces that single knob with a bounded agglomerative physical planner. Direct roots keep the
same similarity order, begin as independent physical groups, and may merge only with an adjacent group
when the exact stored bytes improve and both weighted and per-member read amplification remain <=8x.
Two deterministic merge priorities are auditioned; exact final bytes choose between them and the accepted
attempt-5 archive remains a byte-for-byte fallback.

This changes only encoder-side physical partitioning. It preserves attempt #5's exact graph grammar,
depth-1 dependencies, residual-program format, integrity/recovery semantics and 2 MiB physical ceiling.

Footnote: this file deliberately imports the accepted attempt-5 implementation instead of copying it.
The only monkey-patched seam is v0.28's `_choose_pack_plan`, and that patch exists only while constructing
the experimental graph. Reader code is not patched, so a selected result must verify with the unchanged
attempt-5 reader before it can count as evidence.
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
MAX_ROOTS = 2048
MAX_EXACT_COST_PROBES = 4 * MAX_ROOTS + 16
MERGE_STRATEGIES = ("bytes", "efficiency")

_ORIGINAL_CHOOSE = V028._choose_pack_plan


class _ProbeCap(RuntimeError):
    """Raised when an oracle strategy would exceed its preregistered exact-cost probe budget."""


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _record_cost(raw: bytes) -> int:
    _, payload = V028._compress_record(raw)
    return V028.PH.size + len(payload)


def _group_raw_bytes(group: tuple[int, ...] | list[int], nodes: list[bytes]) -> int:
    return sum(len(nodes[node_id]) for node_id in group)


def _worst_member_amp(groups: list[list[int]] | list[tuple[int, ...]], nodes: list[bytes]) -> float:
    worst = 0.0
    for group in groups:
        raw_bytes = _group_raw_bytes(group, nodes)
        for node_id in group:
            worst = max(worst, raw_bytes / max(1, len(nodes[node_id])))
    return worst


def _ordered_roots(sketches, root_ids: list[int]) -> list[int]:
    """Return v0.28's similarity order mapped back to global node ids."""
    local = V028.similarity_order([sketches[node_id] for node_id in root_ids])
    return [root_ids[index] for index in local]


def _group_metrics(ids: tuple[int, ...], nodes: list[bytes], cache: dict[tuple[int, ...], dict]) -> dict:
    cached = cache.get(ids)
    if cached is not None:
        return cached
    if len(cache) >= MAX_EXACT_COST_PROBES:
        raise _ProbeCap("exact physical-cost probe cap reached")
    raw_bytes = _group_raw_bytes(ids, nodes)
    raw = b"".join(nodes[node_id] for node_id in ids)
    result = {
        "ids": ids,
        "raw_bytes": raw_bytes,
        "members": len(ids),
        "cost": _record_cost(raw),
        "worst_member_amp": max(
            (raw_bytes / max(1, len(nodes[node_id])) for node_id in ids), default=0.0
        ),
    }
    cache[ids] = result
    return result


def _score(strategy: str, saving: int, added_decoded: int, index: int):
    if strategy == "bytes":
        return (saving, -added_decoded, -index)
    if strategy == "efficiency":
        # Footnote: `added_decoded` is the locality price of a merge. A zero-price merge is ordered first;
        # the exact saving and stable left index still break ties deterministically.
        efficiency = float("inf") if added_decoded == 0 else saving / added_decoded
        return (efficiency, saving, -added_decoded, -index)
    raise RuntimeError(f"unknown locality-budget merge strategy: {strategy}")


def _agglomerate(nodes: list[bytes], ordered_roots: list[int], strategy: str):
    """Greedily merge adjacent similarity groups under exact byte and locality accounting.

    Only adjacent groups are eligible, so the inherited similarity ordering never changes. Every *legal*
    new physical record is measured with the real compressor before selection. Because a merge can only
    add locality cost, the planner tracks the exact weighted decoded-byte total and rejects any group whose
    smallest member would experience >8x physical read amplification.

    Footnote: per-member locality is derivable from raw group size and the smallest member, so impossible
    >8x candidates are rejected before level-19 compression. This changes no admissible merge decision; it
    only prevents expensive byte probes for records the locality contract could never permit.

    The cost cache is high leverage: after each accepted merge only its two new neighbor pairings are new
    physical candidates in principle. The simple scan below may revisit old pairs, but those are cache
    hits rather than new level-19 compression probes.
    """
    if len(ordered_roots) > MAX_ROOTS:
        return None, {
            "strategy": strategy,
            "selected": False,
            "skipped": "root-cap",
            "roots": len(ordered_roots),
            "max_roots": MAX_ROOTS,
        }
    if not ordered_roots:
        return (0, 0.0, 0, []), {
            "strategy": strategy,
            "selected": False,
            "skipped": None,
            "roots": 0,
            "merges": 0,
            "exact_cost_probes": 0,
            "bytes": 0,
            "read_amp": 0.0,
            "worst_member_amp": 0.0,
            "max_group_bytes": 0,
        }

    cache: dict[tuple[int, ...], dict] = {}
    groups = [(node_id,) for node_id in ordered_roots]
    try:
        singleton = [_group_metrics(group, nodes, cache) for group in groups]
    except _ProbeCap:
        raise RuntimeError("singleton roots exceeded exact-cost probe cap")

    logical = sum(max(1, len(nodes[node_id])) for node_id in ordered_roots)
    decoded = sum(row["raw_bytes"] * row["members"] for row in singleton)
    max_decoded = int(MAX_READ_AMP * logical)
    total_cost = sum(row["cost"] for row in singleton)
    merges = 0

    while len(groups) > 1:
        best = None
        try:
            for index in range(len(groups) - 1):
                left_ids = groups[index]
                right_ids = groups[index + 1]
                left = _group_metrics(left_ids, nodes, cache)
                right = _group_metrics(right_ids, nodes, cache)
                merged_ids = left_ids + right_ids
                raw_bytes = left["raw_bytes"] + right["raw_bytes"]
                if raw_bytes > MAX_PACK_BYTES:
                    continue

                # Footnote: the future group's worst member is the smallest logical member. This bound
                # needs no compression result, so reject it before spending an exact physical-cost probe.
                smallest_member = min(
                    min((len(nodes[node_id]) for node_id in left_ids), default=1),
                    min((len(nodes[node_id]) for node_id in right_ids), default=1),
                )
                prospective_worst = raw_bytes / max(1, smallest_member)
                if prospective_worst > MAX_READ_AMP + 1e-12:
                    continue

                merged = _group_metrics(merged_ids, nodes, cache)
                saving = left["cost"] + right["cost"] - merged["cost"]
                if saving <= 0:
                    continue
                old_decoded = (
                    left["raw_bytes"] * left["members"] + right["raw_bytes"] * right["members"]
                )
                new_decoded = merged["raw_bytes"] * merged["members"]
                added_decoded = new_decoded - old_decoded
                if decoded + added_decoded > max_decoded:
                    continue
                score = _score(strategy, saving, added_decoded, index)
                if best is None or score > best[0]:
                    best = (score, index, merged_ids, saving, added_decoded)
        except _ProbeCap:
            return None, {
                "strategy": strategy,
                "selected": False,
                "skipped": "exact-cost-probe-cap",
                "roots": len(ordered_roots),
                "merges": merges,
                "exact_cost_probes": len(cache),
                "max_exact_cost_probes": MAX_EXACT_COST_PROBES,
            }

        if best is None:
            break
        _, index, merged_ids, saving, added_decoded = best
        groups[index : index + 2] = [merged_ids]
        total_cost -= saving
        decoded += added_decoded
        merges += 1

    group_lists = [list(group) for group in groups]
    if sorted(node_id for group in group_lists for node_id in group) != sorted(ordered_roots):
        raise RuntimeError("locality-budget agglomeration lost or duplicated a root")
    read_amp = decoded / max(1, logical)
    worst = _worst_member_amp(group_lists, nodes)
    max_group = max((_group_raw_bytes(group, nodes) for group in group_lists), default=0)
    if read_amp > MAX_READ_AMP + 1e-12 or worst > MAX_READ_AMP + 1e-12:
        raise RuntimeError("agglomerative planner violated its read-amplification contract")
    return (total_cost, read_amp, max_group, group_lists), {
        "strategy": strategy,
        "selected": False,
        "skipped": None,
        "roots": len(ordered_roots),
        "merges": merges,
        "exact_cost_probes": len(cache),
        "bytes": total_cost,
        "read_amp": read_amp,
        "worst_member_amp": worst,
        "max_group_bytes": max_group,
    }


def _choose_pack_plan_budgeted(nodes: list[bytes], sketches, root_ids: list[int]):
    """Tournament two bounded locality spend policies against the exact inherited global plan."""
    original, original_trials = _ORIGINAL_CHOOSE(nodes, sketches, root_ids)
    original_cost, original_amp, original_limit, original_groups = original
    original_worst = _worst_member_amp(original_groups, nodes)
    best = original
    best_diag = {
        "strategy": "global-limit-fallback",
        "selected": False,
        "skipped": None,
        "bytes": original_cost,
        "read_amp": original_amp,
        "worst_member_amp": original_worst,
        "original_worst_member_amp": original_worst,
        "max_group_bytes": max((_group_raw_bytes(group, nodes) for group in original_groups), default=0),
        "saving_vs_global": 0,
    }
    diagnostics = []
    order = _ordered_roots(sketches, root_ids)

    for strategy in MERGE_STRATEGIES:
        candidate, diag = _agglomerate(nodes, order, strategy)
        diag["original_worst_member_amp"] = original_worst
        diagnostics.append(diag)
        if candidate is None:
            continue
        cost, amp, max_group, groups = candidate
        worst = float(diag["worst_member_amp"])
        # Footnote: exact ties remain on the established global planner. New physical boundaries must buy
        # real bytes and satisfy both read budgets; otherwise attempt #5 remains untouched.
        if cost < best[0] and amp <= MAX_READ_AMP and worst <= MAX_READ_AMP + 1e-12:
            best = (cost, amp, max_group, groups)
            best_diag = dict(diag)
            best_diag.update({
                "selected": True,
                "saving_vs_global": original_cost - cost,
            })

    trials = [dict(row, strategy="global-limit") for row in original_trials]
    for row in diagnostics:
        trial = dict(row)
        trial["selected"] = bool(
            best_diag.get("selected")
            and row.get("strategy") == best_diag.get("strategy")
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
        "read_amp": 0.0,
        "worst_member_amp": 0.0,
        "original_worst_member_amp": 0.0,
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

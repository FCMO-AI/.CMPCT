"""CMPCT v0.30 research — sparse Multi-View HyperPack compiler.

v0.29 attempt #6 proved that direct-root physical placement still contains useful cross-record entropy,
but its agglomerator can only merge neighbours in one inherited similarity ordering. HyperPack keeps the
same attempt-5 graph grammar and <=8x read-locality contract, while replacing that one-dimensional search
with a bounded sparse graph assembled from several independent similarity views. Exact level-19 stored
bytes remain the only authority for accepting a merge.

The important distinction is that this is not another dictionary or residual codec. It changes which
already-direct roots share a physical compression context. Decoder grammar, dependency depth, residual
programs, integrity, recovery, and logical node identities remain unchanged.

Footnote: the implementation imports attempt #6 and starts from its best exact plan. A HyperPack result
must therefore beat the strongest previously measured locality-budget partition on the same roots;
otherwise the old plan is returned byte-for-byte. New research cannot silently delete a prior win.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
A6_PATH = HERE / "entropygraph_v029_pack_budget.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A6 = _load(A6_PATH, "cmpct_v030_hyperpack_attempt6")
A5 = A6.A5
RAW_A5 = A6.RAW_A5
V028 = A6.V028
BASE = A6.BASE

MAX_READ_AMP = A6.MAX_READ_AMP
MAX_PACK_BYTES = A6.MAX_PACK_BYTES
MAX_ROOTS = A6.MAX_ROOTS
MAX_EXACT_COST_PROBES = 20 * MAX_ROOTS + 96
NEIGHBOR_WINDOW = 3
LSH_MAX_CANDIDATES = 24
LSH_MAX_BUCKET = 96
MIN_PAIR_GAIN = 1
SHADOW_PRICES = (0.0, 1.0 / 16384.0, 1.0 / 8192.0, 1.0 / 4096.0)


class _ProbeCap(RuntimeError):
    pass


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _record_cost(raw: bytes) -> int:
    _, payload = V028._compress_record(raw)
    return V028.PH.size + len(payload)


def _group_raw_bytes(group: tuple[int, ...] | list[int], nodes: list[bytes]) -> int:
    return sum(len(nodes[node_id]) for node_id in group)


def _worst_member_amp(groups, nodes: list[bytes]) -> float:
    worst = 0.0
    for group in groups:
        raw_bytes = _group_raw_bytes(group, nodes)
        for node_id in group:
            worst = max(worst, raw_bytes / max(1, len(nodes[node_id])))
    return worst


def _metrics(ids: tuple[int, ...], nodes: list[bytes], cache: dict[tuple[int, ...], dict]) -> dict:
    # Footnote: physical member order is intentionally part of the cache key. Zstd context is directional,
    # so HyperPack auditions orientation instead of pretending A+B and B+A have identical byte cost.
    key = tuple(ids)
    cached = cache.get(key)
    if cached is not None:
        return cached
    if len(cache) >= MAX_EXACT_COST_PROBES:
        raise _ProbeCap("HyperPack exact-cost probe cap reached")
    raw_bytes = _group_raw_bytes(key, nodes)
    raw = b"".join(nodes[node_id] for node_id in key)
    smallest = min((len(nodes[node_id]) for node_id in key), default=1)
    row = {
        "ids": key,
        "raw_bytes": raw_bytes,
        "members": len(key),
        "cost": _record_cost(raw),
        "worst_member_amp": raw_bytes / max(1, smallest),
    }
    cache[key] = row
    return row


def _add_window_pairs(order: list[int], pairs: set[tuple[int, int]], window: int = NEIGHBOR_WINDOW) -> None:
    for i, left in enumerate(order):
        for j in range(i + 1, min(len(order), i + 1 + window)):
            right = order[j]
            pairs.add((min(left, right), max(left, right)))


def _candidate_pairs(sketches, root_ids: list[int]) -> tuple[set[tuple[int, int]], dict]:
    """Build a sparse deterministic union of independent similarity projections.

    Footnote: candidate generation may be approximate; selection never is. Every accepted edge is priced
    with the real level-19 physical codec, so a sketch collision can waste encoder work but cannot invent a
    compression win.
    """
    pairs: set[tuple[int, int]] = set()
    local_sketches = [sketches[node_id] for node_id in root_ids]

    inherited_local = V028.similarity_order(local_sketches)
    inherited = [root_ids[index] for index in inherited_local]
    _add_window_pairs(inherited, pairs)

    band_count = len(local_sketches[0].features) if local_sketches else 0
    for band in range(band_count):
        order = sorted(
            root_ids,
            key=lambda node_id: (
                sketches[node_id].size_bucket,
                sketches[node_id].features[band],
                node_id,
            ),
        )
        _add_window_pairs(order, pairs)

    size_order = sorted(root_ids, key=lambda node_id: (sketches[node_id].size_bucket, node_id))
    _add_window_pairs(size_order, pairs)

    for edge in V028.lsh_candidates(
        local_sketches, max_bucket=LSH_MAX_BUCKET, max_candidates=LSH_MAX_CANDIDATES
    ):
        a = root_ids[edge.target]
        b = root_ids[edge.base]
        if a != b:
            pairs.add((min(a, b), max(a, b)))

    return pairs, {
        "candidate_pairs": len(pairs),
        "views": 2 + band_count,
        "band_views": band_count,
        "neighbor_window": NEIGHBOR_WINDOW,
    }


def _pair_graph(nodes: list[bytes], sketches, root_ids: list[int], cache: dict) -> tuple[dict[int, set[int]], dict]:
    pairs, diag = _candidate_pairs(sketches, root_ids)
    neighbors = {node_id: set() for node_id in root_ids}
    profitable = 0
    skipped_locality = 0
    for left, right in sorted(pairs):
        l = _metrics((left,), nodes, cache)
        r = _metrics((right,), nodes, cache)
        raw_bytes = l["raw_bytes"] + r["raw_bytes"]
        smallest = min(len(nodes[left]), len(nodes[right]))
        if raw_bytes > MAX_PACK_BYTES or raw_bytes / max(1, smallest) > MAX_READ_AMP + 1e-12:
            skipped_locality += 1
            continue
        try:
            forward = _metrics((left, right), nodes, cache)
            reverse = _metrics((right, left), nodes, cache)
            merged = min((forward, reverse), key=lambda row: (row["cost"], row["ids"]))
        except _ProbeCap:
            break
        saving = l["cost"] + r["cost"] - merged["cost"]
        if saving >= MIN_PAIR_GAIN:
            neighbors[left].add(right)
            neighbors[right].add(left)
            profitable += 1
    diag.update({
        "profitable_pair_edges": profitable,
        "pair_locality_rejects": skipped_locality,
        "pair_probe_count": len(cache),
    })
    return neighbors, diag


def _groups_neighbors(group: tuple[int, ...], member_neighbors: dict[int, set[int]],
                      owner: dict[int, int], index: int) -> set[int]:
    out: set[int] = set()
    for member in group:
        for neighbor in member_neighbors.get(member, ()):
            other = owner.get(neighbor)
            if other is not None and other != index:
                out.add(other)
    return out


def _optimize(nodes: list[bytes], root_ids: list[int], member_neighbors: dict[int, set[int]],
              cache: dict, shadow_price: float):
    """Greedy sparse hypergraph contraction under exact byte and locality accounting."""
    groups = [(node_id,) for node_id in root_ids]
    logical = sum(max(1, len(nodes[node_id])) for node_id in root_ids)
    decoded = sum(len(nodes[node_id]) for node_id in root_ids)
    max_decoded = int(MAX_READ_AMP * logical)
    merges = 0

    while len(groups) > 1:
        owner = {member: index for index, group in enumerate(groups) for member in group}
        best = None
        seen: set[tuple[int, int]] = set()
        for i, left_ids in enumerate(groups):
            for j in _groups_neighbors(left_ids, member_neighbors, owner, i):
                if j <= i or (i, j) in seen:
                    continue
                seen.add((i, j))
                right_ids = groups[j]
                forward_ids = left_ids + right_ids
                reverse_ids = right_ids + left_ids
                raw_bytes = _group_raw_bytes(forward_ids, nodes)
                if raw_bytes > MAX_PACK_BYTES:
                    continue
                smallest = min(len(nodes[node_id]) for node_id in forward_ids)
                worst = raw_bytes / max(1, smallest)
                if worst > MAX_READ_AMP + 1e-12:
                    continue
                try:
                    left = _metrics(left_ids, nodes, cache)
                    right = _metrics(right_ids, nodes, cache)
                    forward = _metrics(forward_ids, nodes, cache)
                    reverse = _metrics(reverse_ids, nodes, cache)
                    merged = min((forward, reverse), key=lambda row: (row["cost"], row["ids"]))
                    merged_ids = merged["ids"]
                except _ProbeCap:
                    return None, {
                        "skipped": "exact-cost-probe-cap",
                        "merges": merges,
                        "exact_cost_probes": len(cache),
                    }
                saving = left["cost"] + right["cost"] - merged["cost"]
                if saving <= 0:
                    continue
                old_decoded = left["raw_bytes"] * left["members"] + right["raw_bytes"] * right["members"]
                new_decoded = merged["raw_bytes"] * merged["members"]
                added_decoded = new_decoded - old_decoded
                if decoded + added_decoded > max_decoded:
                    continue
                score = saving - shadow_price * added_decoded
                if score <= 0 and shadow_price > 0:
                    continue
                rank = (score, saving, -added_decoded, -len(merged_ids), -i, -j)
                if best is None or rank > best[0]:
                    best = (rank, i, j, merged_ids, saving, added_decoded)
        if best is None:
            break
        _, i, j, merged_ids, _, added_decoded = best
        groups[i] = merged_ids
        del groups[j]
        decoded += added_decoded
        merges += 1

    cost = sum(_metrics(group, nodes, cache)["cost"] for group in groups)
    read_amp = decoded / max(1, logical)
    worst = _worst_member_amp(groups, nodes)
    max_group = max((_group_raw_bytes(group, nodes) for group in groups), default=0)
    return (cost, read_amp, max_group, [list(group) for group in groups]), {
        "skipped": None,
        "shadow_price": shadow_price,
        "groups": len(groups),
        "merges": merges,
        "bytes": cost,
        "read_amp": read_amp,
        "worst_member_amp": worst,
        "max_group_bytes": max_group,
        "exact_cost_probes": len(cache),
    }


def _choose_pack_plan_hyper(nodes: list[bytes], sketches, root_ids: list[int]):
    """Tournament HyperPack plans against attempt #6's already stronger exact partition."""
    inherited, inherited_trials = A6._choose_pack_plan_budgeted(nodes, sketches, root_ids)
    inherited_cost, _, _, _ = inherited
    if len(root_ids) > MAX_ROOTS or not root_ids:
        return inherited, inherited_trials

    cache: dict[tuple[int, ...], dict] = {}
    try:
        for node_id in root_ids:
            _metrics((node_id,), nodes, cache)
        member_neighbors, graph_diag = _pair_graph(nodes, sketches, root_ids, cache)
    except _ProbeCap:
        return inherited, inherited_trials + [{
            "strategy": "hyperpack-summary",
            "selected": False,
            "skipped": "pair-probe-cap",
            "saving_vs_attempt6": 0,
            "exact_cost_probes": len(cache),
        }]

    best = inherited
    best_diag = None
    trials = list(inherited_trials)
    for shadow in SHADOW_PRICES:
        candidate, diag = _optimize(nodes, root_ids, member_neighbors, cache, shadow)
        diag = dict(graph_diag, **diag)
        diag["strategy"] = f"hyperpack-shadow-{shadow:.8f}"
        diag["selected"] = False
        trials.append(diag)
        if candidate is not None and candidate[0] < best[0]:
            best = candidate
            best_diag = diag

    if best_diag is not None:
        best_diag["selected"] = True
    summary = {
        "strategy": "hyperpack-summary",
        "selected": best[0] < inherited_cost,
        "skipped": None,
        "attempt6_bytes": inherited_cost,
        "bytes": best[0],
        "saving_vs_attempt6": inherited_cost - best[0],
        "candidate_pairs": graph_diag["candidate_pairs"],
        "profitable_pair_edges": graph_diag["profitable_pair_edges"],
        "exact_cost_probes": len(cache),
        "read_amp": best[1],
        "max_group_bytes": best[2],
        "worst_member_amp": _worst_member_amp(best[3], nodes),
        "shadow_prices": list(SHADOW_PRICES),
    }
    trials.append(summary)
    return best, trials


def _build_hyper_graph(root: Path, out: Path) -> dict:
    previous = V028._choose_pack_plan
    V028._choose_pack_plan = _choose_pack_plan_hyper
    try:
        stats = RAW_A5._build_graph(root, out)
    finally:
        V028._choose_pack_plan = previous
    summary = next(
        (row for row in stats.get("pack_trials", []) if row.get("strategy") == "hyperpack-summary"),
        None,
    )
    stats["hyperpack"] = summary or {"selected": False, "saving_vs_attempt6": 0}
    return stats


def build_graph(root: Path, out: Path) -> dict:
    return _build_hyper_graph(root, out)


def build(root: Path, out: Path) -> dict:
    """Tournament the new physical plan against accepted attempt #5; exact smaller artifact wins."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-hyperpack-") as td:
        temp = Path(td)
        attempt5_path = temp / "attempt5.cmpct"
        hyper_path = temp / "hyperpack.cmpct"
        attempt5_stats = A5.build(root, attempt5_path)
        hyper_started = time.perf_counter()
        hyper_stats = _build_hyper_graph(root, hyper_path)
        hyper_create_s = time.perf_counter() - hyper_started

        if hyper_path.stat().st_size < attempt5_path.stat().st_size:
            shutil.copyfile(hyper_path, out)
            selected = "hyperpack"
        else:
            shutil.copyfile(attempt5_path, out)
            selected = "attempt5-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "attempt5_bytes": attempt5_path.stat().st_size,
            "hyperpack_bytes": hyper_path.stat().st_size,
            "saving_vs_attempt5": attempt5_path.stat().st_size - out.stat().st_size,
            "portfolio_create_s": time.perf_counter() - started,
            "hyperpack_create_s": hyper_create_s,
            "attempt5": attempt5_stats,
            "hyperpack": hyper_stats,
        }


def extract(archive: Path, dst: Path) -> None:
    A5.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return A5.strong_verify(archive)


def run(root: Path, work_root: Path, output: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    archive = work_root / "candidate.cmpct"
    stats = build(root, archive)
    verify = strong_verify(archive)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-hyperpack-extract-") as td:
        dst = Path(td)
        extract(archive, dst)
        exact = treehash(dst) == treehash(root)
    result = {
        "schema": "cmpct-v030-hyperpack-v1",
        "source_tree_sha256": treehash(root),
        "archive_sha256": __import__("hashlib").sha256(archive.read_bytes()).hexdigest(),
        "exact_roundtrip": exact,
        "strong_verify": verify,
        "stats": stats,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.work_root, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["exact_roundtrip"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

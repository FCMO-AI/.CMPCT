from __future__ import annotations

"""Exact A/B for a generic upper-bound terminal in EntropyGraph whole-object splice search.

The historical algorithm can select a parent only when non-overlapping whole-child matches cover at least
128 KiB. Before inspecting parent bytes, the sum of *all* eligible smaller child sizes is therefore a strict
upper bound on selectable coverage. If that sum is below the threshold, no sequence of bytes.find calls can
possibly promote the parent and every search for that parent is provably dead work.

This oracle does not change the engine. It reproduces the historical splice search and compares it with that
content-agnostic mathematical terminal on the frozen Office normalized stage. Promotion here is research-only:
exact splice-graph identity plus material search/time reduction can authorize an engine patch, never release credit.
"""

import argparse
import json
from pathlib import Path
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as OFFICE

MIN_OBJECT = 32 * 1024
MIN_SELECTED_COVERAGE = 128 * 1024
ROUNDS = 11


def _files_and_raws(stage: Path) -> tuple[list[Path], dict[Path, bytes]]:
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    raws = {p: p.read_bytes() for p in files}
    candidates = [p for p in files if len(raws[p]) >= MIN_OBJECT]
    return candidates, raws


def _choose(parent: Path, children: list[Path], raws: dict[Path, bytes]) -> tuple[list[tuple[int, int, Path]], int]:
    pr = raws[parent]
    hits: list[tuple[int, int, Path]] = []
    calls = 0
    for child in children:
        calls += 1
        pos = pr.find(raws[child])
        if pos >= 0:
            hits.append((pos, pos + len(raws[child]), child))
    hits.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    chosen: list[tuple[int, int, Path]] = []
    end = -1
    for hit in hits:
        if hit[0] >= end:
            chosen.append(hit)
            end = hit[1]
    if sum(e - s for s, e, _ in chosen) < MIN_SELECTED_COVERAGE:
        chosen = []
    return chosen, calls


def _run_search(candidates: list[Path], raws: dict[Path, bytes], terminal: bool) -> tuple[dict[Path, list[tuple[int, int, Path]]], int, int]:
    splice: dict[Path, list[tuple[int, int, Path]]] = {}
    calls = 0
    terminal_parents = 0
    for parent in candidates:
        pr_len = len(raws[parent])
        children = [child for child in candidates if child != parent and len(raws[child]) < pr_len]
        if terminal and sum(len(raws[child]) for child in children) < MIN_SELECTED_COVERAGE:
            terminal_parents += 1
            continue
        chosen, child_calls = _choose(parent, children, raws)
        calls += child_calls
        if chosen:
            splice[parent] = chosen
    return splice, calls, terminal_parents


def _signature(splice: dict[Path, list[tuple[int, int, Path]]], stage: Path) -> list:
    return [
        [
            parent.relative_to(stage).as_posix(),
            [[s, e, child.relative_to(stage).as_posix()] for s, e, child in hits],
        ]
        for parent, hits in sorted(splice.items(), key=lambda row: row[0].relative_to(stage).as_posix())
    ]


def run(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    source, _accepted_v029 = OFFICE._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-office-splice-bound-", dir=work_root) as td:
        root = Path(td)
        stage = OFFICE.EXT._normalized_stage(source, root / "normalized")
        candidates, raws = _files_and_raws(stage)

        baseline_samples: list[float] = []
        candidate_samples: list[float] = []
        baseline_result = candidate_result = None
        baseline_calls = candidate_calls = terminal_parents = -1
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for terminal in order:
                started = time.perf_counter()
                result, calls, terminals = _run_search(candidates, raws, terminal)
                elapsed = time.perf_counter() - started
                if terminal:
                    candidate_samples.append(elapsed)
                    candidate_result, candidate_calls, terminal_parents = result, calls, terminals
                else:
                    baseline_samples.append(elapsed)
                    baseline_result, baseline_calls = result, calls

        assert baseline_result is not None and candidate_result is not None
        baseline_sig = _signature(baseline_result, stage)
        candidate_sig = _signature(candidate_result, stage)
        exact = baseline_sig == candidate_sig
        baseline_median = float(statistics.median(baseline_samples))
        candidate_median = float(statistics.median(candidate_samples))
        call_reduction = 1.0 - candidate_calls / max(baseline_calls, 1)
        time_reduction = 1.0 - candidate_median / max(baseline_median, 1e-12)
        promotion = exact and call_reduction >= 0.10 and time_reduction >= 0.10

        return {
            "schema": "cmpct-v030-office-splice-upper-bound-v1",
            "rounds": ROUNDS,
            "candidate_count": len(candidates),
            "selected_parent_count": len(baseline_result),
            "baseline_find_calls": baseline_calls,
            "candidate_find_calls": candidate_calls,
            "provably_terminal_parent_count": terminal_parents,
            "find_call_reduction_fraction": call_reduction,
            "baseline_median_s": baseline_median,
            "candidate_median_s": candidate_median,
            "search_time_reduction_fraction": time_reduction,
            "exact_splice_graph_identity": exact,
            "splice_signature": baseline_sig,
            "contract": {
                "minimum_object_bytes": MIN_OBJECT,
                "minimum_selected_coverage_bytes": MIN_SELECTED_COVERAGE,
                "terminal_is_size_upper_bound_only": True,
                "benchmark_identity_used": False,
                "path_identity_used": False,
                "minimum_find_call_reduction_fraction": 0.10,
                "minimum_time_reduction_fraction": 0.10,
                "release_credit": False,
            },
            "promotion_signal": promotion,
            "release_credit": False,
            "claim_boundary": (
                "Research-only exact algorithm A/B. A promotion signal authorizes testing the generic mathematical "
                "upper-bound terminal inside the historical engine with complete archive-byte/generalization evidence."
            ),
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-office-splice-bound-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-office-splice-bound.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "candidate_count", "selected_parent_count", "baseline_find_calls", "candidate_find_calls",
        "provably_terminal_parent_count", "find_call_reduction_fraction", "baseline_median_s",
        "candidate_median_s", "search_time_reduction_fraction", "exact_splice_graph_identity", "promotion_signal"
    )}, indent=2), flush=True)
    if not result["exact_splice_graph_identity"]:
        raise SystemExit("upper-bound terminal changed the splice graph")


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Five-workload complete-artifact portfolio for orthogonal CMPCT v0.30 research mechanisms.

This benchmark does **not** invent a hybrid grammar and does not add independent headline numbers on paper.
For each frozen source tree it actually builds accepted v0.29, self-contained CMPNX14 Geometry IR, and—when
its documented file-count/file-size contract permits it—the exact green PrefixGraph oracle.  Every built
candidate must independently strong-verify to the same authenticated logical tree.  Only then does an exact
complete-file byte tournament select the row winner.

The gate deliberately inherits both prior mechanism contracts rather than weakening either one:
- PrefixGraph must still save >=24 KiB over its two historical rows, >=2 KiB on each row, at depth <=1;
- GIR must still save >=2 MiB over its three structured rows, >=256 KiB on every row;
- therefore the five-row exact portfolio must save >=2 MiB + 24 KiB = 2,121,728 bytes, improve 5/5 rows,
  regress 0, and visibly retain both mechanism families among exact winners.

Footnote: this is a *portfolio coexistence* experiment, not same-archive composition evidence.  A future
single grammar must still pay any integration metadata/reference/locality costs directly and cannot cite the
portfolio total as its own compression result.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import gir_v030_focused_complete as gir_gate
from benchmarks import prefixgraph_v030_oracle as pg_gate
from experiments import entropygraph_v030_gir_safe as GIR
from experiments import entropygraph_v030_prefixgraph as PG

STRUCTURAL = tuple(pg_gate.TARGETS)
STRUCTURED = tuple(gir_gate.EXPECTED)
TARGETS = STRUCTURAL + STRUCTURED

MIN_PREFIX_AGGREGATE = pg_gate.MIN_AGGREGATE_SAVING
MIN_PREFIX_EACH = pg_gate.MIN_EACH_SAVING
MIN_GIR_AGGREGATE = gir_gate.MIN_AGGREGATE_SAVING
MIN_GIR_EACH = gir_gate.MIN_ROW_SAVING
MIN_PORTFOLIO_AGGREGATE = MIN_PREFIX_AGGREGATE + MIN_GIR_AGGREGATE

# Deterministic ties are conservative: unchanged accepted v0.29 wins an exact tie, then GIR, then PrefixGraph.
# A new representation therefore receives no credit merely for matching inherited bytes.
SELECTION_PRIORITY = {"v029": 0, "gir": 1, "prefixgraph": 2}


def _prefix_eligibility(root: Path) -> tuple[bool, str | None]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not 1 <= len(files) <= PG.MAX_FILES:
        return False, f"file_count={len(files)} outside 1..{PG.MAX_FILES}"
    too_large = [path for path in files if path.stat().st_size > PG.MAX_FILE_BYTES]
    if too_large:
        largest = max(path.stat().st_size for path in too_large)
        return False, f"file_size={largest} exceeds {PG.MAX_FILE_BYTES}"
    return True, None


def _select_complete_artifact(candidate_bytes: dict[str, int]) -> str:
    if "v029" not in candidate_bytes:
        raise ValueError("portfolio selection requires accepted v0.29 floor")
    return min(candidate_bytes, key=lambda name: (candidate_bytes[name], SELECTION_PRIORITY[name]))


def _generate_sources(work_root: Path) -> dict[str, Path]:
    corpus_parent = work_root / "corpora"
    structural_parent = corpus_parent / "structural"
    structural_parent.mkdir(parents=True, exist_ok=True)
    pg_gate.corpus.shifted_versions(structural_parent)
    pg_gate.corpus.boundary_churn(structural_parent)

    roots: dict[str, Path] = {name: structural_parent / name for name in STRUCTURAL}
    structured_parent = corpus_parent / "structured"
    for name in STRUCTURED:
        roots[name] = gir_gate._generate(structured_parent, name)

    controls = pg_gate._accepted_rows()
    for name, root in roots.items():
        gir_tree = GIR.treehash(root)
        pg_tree = PG.treehash(root)
        expected = controls[name]["tree_sha256"] if name in controls else gir_gate.EXPECTED[name]
        if gir_tree != expected or pg_tree != expected:
            raise RuntimeError(
                f"portfolio source identity drift for {name}: expected={expected}, gir={gir_tree}, pg={pg_tree}"
            )
    return roots


def _verify(name: str, engine, archive: Path, expected_tree: str) -> dict:
    result = engine.strong_verify(archive)
    if not result.get("ok") or result.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{name} strong verification failed: {result}")
    return result


def _run_row(root: Path, archive_root: Path, structural_controls: dict[str, dict]) -> dict:
    row_root = archive_root / root.name
    row_root.mkdir(parents=True, exist_ok=True)
    expected_tree = (
        structural_controls[root.name]["tree_sha256"]
        if root.name in structural_controls
        else gir_gate.EXPECTED[root.name]
    )

    base_path = row_root / "accepted-v029.cmpct"
    gir_path = row_root / "geometry-ir.cmpct"
    pg_path = row_root / "prefixgraph.cmpct"

    started = time.perf_counter()
    base_stats = GIR.BASE.build(root, base_path)
    base_create_s = time.perf_counter() - started
    base_verify = _verify("accepted v0.29", GIR.BASE, base_path, expected_tree)
    base_bytes = base_path.stat().st_size
    if root.name in structural_controls:
        accepted = int(structural_controls[root.name]["candidate_bytes"])
        if base_bytes != accepted:
            raise RuntimeError(f"accepted v0.29 byte drift for {root.name}: {base_bytes} != {accepted}")

    started = time.perf_counter()
    gir_stats = GIR._build_gir(root, gir_path)
    gir_create_s = time.perf_counter() - started
    gir_verify = _verify("CMPNX14 GIR", GIR, gir_path, expected_tree)
    gir_bytes = gir_path.stat().st_size

    pg_eligible, pg_ineligible_reason = _prefix_eligibility(root)
    pg_stats = None
    pg_create_s = None
    pg_verify = None
    pg_bytes = None
    if pg_eligible:
        started = time.perf_counter()
        pg_stats = PG.build(root, pg_path)
        pg_create_s = time.perf_counter() - started
        pg_verify = _verify("PrefixGraph", PG, pg_path, expected_tree)
        pg_bytes = pg_path.stat().st_size

    candidate_bytes = {"v029": base_bytes, "gir": gir_bytes}
    if pg_bytes is not None:
        candidate_bytes["prefixgraph"] = pg_bytes
    selected = _select_complete_artifact(candidate_bytes)
    selected_bytes = candidate_bytes[selected]

    row = {
        "name": root.name,
        "class": "structural" if root.name in STRUCTURAL else "structured",
        "tree_sha256": expected_tree,
        "logical_bytes": sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
        "files": sum(1 for path in root.rglob("*") if path.is_file()),
        "v029_bytes": base_bytes,
        "gir_bytes": gir_bytes,
        "prefixgraph_bytes": pg_bytes,
        "prefixgraph_eligible": pg_eligible,
        "prefixgraph_ineligible_reason": pg_ineligible_reason,
        "selected": selected,
        "candidate_bytes": selected_bytes,
        "saving_vs_v029_bytes": base_bytes - selected_bytes,
        "gir_saving_vs_v029_bytes": base_bytes - gir_bytes,
        "prefixgraph_saving_vs_v029_bytes": None if pg_bytes is None else base_bytes - pg_bytes,
        "create_s": {
            "v029": base_create_s,
            "gir": gir_create_s,
            "prefixgraph": pg_create_s,
        },
        "accepted_v029_selected": base_stats.get("selected"),
        "gir_node_kind_counts": gir_stats.get("node_kind_counts"),
        "gir_hierarchical_prefix_nodes": int(gir_stats.get("hierarchical_prefix_nodes", 0)),
        "prefix_records": None if pg_stats is None else int(pg_stats["prefix_records"]),
        "prefix_anchor": None if pg_stats is None else pg_stats["anchor"],
        "prefix_max_dependency_depth": None if pg_stats is None else int(pg_stats["max_dependency_depth"]),
        "strong_verify": {
            "v029": base_verify,
            "gir": gir_verify,
            "prefixgraph": pg_verify,
        },
    }
    print(json.dumps(row, sort_keys=True, default=str), flush=True)
    return row


def _gate(rows: list[dict]) -> dict:
    by_name = {row["name"]: row for row in rows}
    prefix_rows = [by_name[name] for name in STRUCTURAL]
    gir_rows = [by_name[name] for name in STRUCTURED]

    prefix_saving = sum(int(row["prefixgraph_saving_vs_v029_bytes"] or 0) for row in prefix_rows)
    prefix_gate = (
        prefix_saving >= MIN_PREFIX_AGGREGATE
        and all(row["prefixgraph_eligible"] for row in prefix_rows)
        and all(int(row["prefixgraph_saving_vs_v029_bytes"] or 0) >= MIN_PREFIX_EACH for row in prefix_rows)
        and all(int(row["prefix_records"] or 0) > 0 for row in prefix_rows)
        and all(int(row["prefix_max_dependency_depth"] or 99) <= 1 for row in prefix_rows)
    )

    gir_saving = sum(row["gir_saving_vs_v029_bytes"] for row in gir_rows)
    gir_gate_ok = (
        gir_saving >= MIN_GIR_AGGREGATE
        and all(row["gir_saving_vs_v029_bytes"] >= MIN_GIR_EACH for row in gir_rows)
    )

    portfolio_saving = sum(row["saving_vs_v029_bytes"] for row in rows)
    selected_mechanisms = {row["selected"] for row in rows}
    coexistence = (
        all(by_name[name]["selected"] == "prefixgraph" for name in STRUCTURAL)
        and any(by_name[name]["selected"] == "gir" for name in STRUCTURED)
    )
    portfolio_gate = (
        prefix_gate
        and gir_gate_ok
        and coexistence
        and portfolio_saving >= MIN_PORTFOLIO_AGGREGATE
        and all(row["saving_vs_v029_bytes"] > 0 for row in rows)
        and "v029" not in selected_mechanisms
    )
    return {
        "prefixgraph_frozen_gate": prefix_gate,
        "prefixgraph_two_row_saving_bytes": prefix_saving,
        "gir_frozen_gate": gir_gate_ok,
        "gir_three_row_saving_bytes": gir_saving,
        "coexistence_gate": coexistence,
        "selected_mechanisms": sorted(selected_mechanisms),
        "portfolio_saving_bytes": portfolio_saving,
        "minimum_portfolio_saving_bytes": MIN_PORTFOLIO_AGGREGATE,
        "workloads_improved": sum(row["saving_vs_v029_bytes"] > 0 for row in rows),
        "workloads_regressed": sum(row["candidate_bytes"] > row["v029_bytes"] for row in rows),
        "portfolio_gate": portfolio_gate,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = _generate_sources(work_root)
    controls = pg_gate._accepted_rows()
    archive_root = work_root / "archives"
    rows = [_run_row(roots[name], archive_root, controls) for name in TARGETS]
    gate = _gate(rows)
    return {
        "schema": "cmpct-v030-mechanism-portfolio-v1",
        "status": "RESEARCH_PORTFOLIO_NOT_SINGLE_GRAMMAR_NOT_RELEASE",
        "claim_boundary": (
            "Five exact public source trees; complete independent archives are tournamented per workload. "
            "This proves or falsifies mechanism coexistence at portfolio level only, not an integrated v0.30 grammar."
        ),
        "contract": {
            "targets": list(TARGETS),
            "structural_targets": list(STRUCTURAL),
            "structured_targets": list(STRUCTURED),
            "minimum_prefixgraph_aggregate_saving_bytes": MIN_PREFIX_AGGREGATE,
            "minimum_prefixgraph_each_saving_bytes": MIN_PREFIX_EACH,
            "maximum_prefixgraph_dependency_depth": 1,
            "minimum_gir_aggregate_saving_bytes": MIN_GIR_AGGREGATE,
            "minimum_gir_each_saving_bytes": MIN_GIR_EACH,
            "minimum_portfolio_aggregate_saving_bytes": MIN_PORTFOLIO_AGGREGATE,
            "workloads_must_improve": len(TARGETS),
            "regression_tolerance_bytes": 0,
            "exact_ties_choose_v029": True,
            "strong_verify_every_built_candidate": True,
            "same_tree_identity_across_all_engines": True,
        },
        "rows": rows,
        "totals": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True), flush=True)
    if not result["totals"]["portfolio_gate"]:
        raise SystemExit("v0.30 mechanism portfolio failed preregistered coexistence gate")


if __name__ == "__main__":
    main()

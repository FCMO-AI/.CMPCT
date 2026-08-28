from __future__ import annotations

"""Fresh-process r24 floor isolation oracle for the Shifted v0.30 RSS blocker.

Prior exact experiments falsified PrefixGraph worker throttling, r24/profile scheduling, r25 candidate serialization,
and bounded r24 finalization as sufficient explanations for the full-product Shifted RSS peak. The remaining
pattern is consistent with allocator high-water: r24 construction itself reaches a large peak, then the same Python
process later retains mapped arenas while r25 work raises the process maximum again.

This oracle changes no shipping code. It runs the exact promoted product in fresh worker processes and compares it
with an experimental composition where the exact shipping r24 floor is built by a short-lived child process. The
child returns only the finished archive and stats; the parent keeps ordinary r25 grammar, selection, verification,
locality and publication semantics. Archive SHA/tree identity is mandatory. Because r24 and r25 may overlap in the
experimental composition, child RSS is reported separately and a conservative parent+child upper bound is also
reported; no memory is hidden and this oracle grants zero release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 2


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _peak_rss_kib(who: int = resource.RUSAGE_SELF) -> int:
    return int(resource.getrusage(who).ru_maxrss)


def _child_r24(source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product

    baseline = _peak_rss_kib()
    started = time.perf_counter()
    stats = dict(product._locality_bounded_r24_build(source, archive))
    wall_s = time.perf_counter() - started
    peak = _peak_rss_kib()
    return {
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "wall_s": wall_s,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": max(0, peak - baseline),
        "stats": stats,
    }


def _install_isolated_r24(product, reports: list[dict]) -> None:
    from experiments import entropygraph_v030_release_product_base as base

    # Prevent the existing in-process prebuild thread from allocating the r24 floor before our patched r24 hook.
    # The ordinary canonical tournament may still overlap the child r24 process with parent-side r25 work; this is
    # intentional and is why the evidence reports a conservative combined RSS upper bound rather than pretending
    # the child is free.
    base.C._prepare_profile_tree = base._ORIGINAL_PREPARE_PROFILE_TREE

    def isolated_r24(root: Path, out: Path) -> dict:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        proc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--r24-child",
                "--source",
                str(root),
                "--archive",
                str(out),
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError(f"isolated r24 child produced no evidence: {proc.stderr}")
        report = json.loads(lines[-1])
        if report["archive_sha256"] != _sha256_file(Path(out)):
            raise RuntimeError("isolated r24 child archive changed after child exit")
        reports.append(report)
        return dict(report["stats"])

    base.C._r24_build = isolated_r24


def _worker(mode: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product

    child_reports: list[dict] = []
    if mode == "isolated-r24":
        _install_isolated_r24(product, child_reports)
    elif mode != "shipping":
        raise ValueError(mode)

    baseline = _peak_rss_kib()
    started = time.perf_counter()
    stats = dict(product.build(source, archive))
    wall_s = time.perf_counter() - started
    peak = _peak_rss_kib()

    verified = dict(product.strong_verify(archive))
    product_tree = product.treehash(source)
    if not verified.get("ok") or verified.get("tree_sha256") != product_tree:
        raise RuntimeError(f"{mode} archive failed strong verification: {verified!r}")

    child_peak = max((int(row["peak_rss_kib"]) for row in child_reports), default=0)
    child_incremental = max((int(row["incremental_peak_rss_kib"]) for row in child_reports), default=0)
    parent_incremental = max(0, peak - baseline)
    return {
        "mode": mode,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        # This is the release-product semantic tree domain used by strong_verify. The accepted frozen corpus uses
        # a separate historical benchmark-tree domain; run() validates that identity independently before workers
        # start. Conflating the two hashes made v1 reject both shipping and isolated modes despite each archive
        # already proving exact semantic identity against product.treehash(source).
        "tree_sha256": product_tree,
        "wall_s": wall_s,
        "parent_baseline_rss_kib": baseline,
        "parent_peak_rss_kib": peak,
        "parent_incremental_peak_rss_kib": parent_incremental,
        "child_peak_rss_kib": child_peak,
        "child_incremental_peak_rss_kib": child_incremental,
        "conservative_combined_incremental_upper_bound_kib": parent_incremental + child_incremental,
        "child_reports": child_reports,
        "build_stats": stats,
    }


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-mode",
            mode,
            "--source",
            str(source),
            "--archive",
            str(archive),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    accepted = GENERAL._accepted_v029_rows()[TARGET]
    expected_historical_tree = str(accepted["tree_sha256"])
    actual_historical_tree = GENERAL._historical_treehash(source)
    if actual_historical_tree != expected_historical_tree:
        raise RuntimeError("Shifted source tree does not match the accepted frozen identity")

    by_mode = {"shipping": [], "isolated-r24": []}
    order = ("shipping", "isolated-r24", "isolated-r24", "shipping")
    for index, mode in enumerate(order):
        archive = work_root / f"{index:02d}-{mode}.cmpct"
        row = _run_worker(mode, source, archive)
        by_mode[mode].append(row)

    all_rows = by_mode["shipping"] + by_mode["isolated-r24"]
    if len({row["archive_sha256"] for row in all_rows}) != 1:
        raise RuntimeError("fresh-process r24 isolation changed complete product archive bytes")
    if len({int(row["archive_bytes"]) for row in all_rows}) != 1:
        raise RuntimeError("fresh-process r24 isolation changed complete product archive size")
    product_trees = {row["tree_sha256"] for row in all_rows}
    if len(product_trees) != 1:
        raise RuntimeError("fresh-process r24 isolation changed complete product semantic tree identity")

    shipping_rss = _median(by_mode["shipping"], "parent_incremental_peak_rss_kib")
    isolated_parent_rss = _median(by_mode["isolated-r24"], "parent_incremental_peak_rss_kib")
    isolated_upper = _median(by_mode["isolated-r24"], "conservative_combined_incremental_upper_bound_kib")
    shipping_wall = _median(by_mode["shipping"], "wall_s")
    isolated_wall = _median(by_mode["isolated-r24"], "wall_s")

    parent_ratio = isolated_parent_rss / max(1.0, shipping_rss)
    conservative_upper_ratio = isolated_upper / max(1.0, shipping_rss)
    wall_ratio = isolated_wall / max(1e-9, shipping_wall)
    allocator_highwater_signal = parent_ratio <= 0.75

    return {
        "schema": "cmpct-v030-r24-fresh-process-rss-v2",
        "target": "/".join(TARGET),
        "rounds_per_mode": ROUNDS,
        "order": list(order),
        "expected_historical_tree_sha256": expected_historical_tree,
        "actual_historical_tree_sha256": actual_historical_tree,
        "product_semantic_tree_sha256": next(iter(product_trees)),
        "tree_identity_domains_separate": True,
        "accepted_v029_bytes": int(accepted["archive_bytes"]),
        "rows": by_mode,
        "shipping_median_parent_incremental_peak_rss_kib": shipping_rss,
        "isolated_median_parent_incremental_peak_rss_kib": isolated_parent_rss,
        "isolated_median_conservative_combined_incremental_upper_bound_kib": isolated_upper,
        "parent_rss_ratio_vs_shipping": parent_ratio,
        "conservative_combined_upper_bound_ratio_vs_shipping": conservative_upper_ratio,
        "shipping_median_wall_s": shipping_wall,
        "isolated_median_wall_s": isolated_wall,
        "wall_ratio_vs_shipping": wall_ratio,
        "allocator_highwater_signal": allocator_highwater_signal,
        "promotion_signal": False,
        "release_credit": False,
        "experiment_valid": True,
        "contract": {
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "selector_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
            "recovery_changed": False,
            "rss_accounting_hides_child": False,
            "parent_signal_threshold_ratio": 0.75,
            "next_gate_if_signal": "implement total-process-accounted child boundary then re-earn authoritative runtime",
        },
        "claim_boundary": (
            "Research-only allocator-high-water diagnostic. Frozen-corpus identity is checked in the historical "
            "benchmark-tree domain; archive semantic identity is checked independently in the release-product tree "
            "domain. A lower parent RSS may justify a separately accounted subprocess architecture, but child memory "
            "is reported explicitly and this result cannot itself change shipping."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-mode", choices=("shipping", "isolated-r24"))
    parser.add_argument("--r24-child", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()

    if args.r24_child:
        if args.source is None or args.archive is None:
            parser.error("--r24-child requires --source and --archive")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(_child_r24(args.source, args.archive), separators=(",", ":"), default=str), flush=True)
        return
    if args.worker_mode:
        if args.source is None or args.archive is None:
            parser.error("--worker-mode requires --source and --archive")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(_worker(args.worker_mode, args.source, args.archive), separators=(",", ":"), default=str), flush=True)
        return
    if args.work_root is None or args.output is None:
        parser.error("oracle mode requires --work-root and --output")
    evidence = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "parent_rss_ratio_vs_shipping": evidence["parent_rss_ratio_vs_shipping"],
        "conservative_upper_ratio": evidence["conservative_combined_upper_bound_ratio_vs_shipping"],
        "wall_ratio_vs_shipping": evidence["wall_ratio_vs_shipping"],
        "allocator_highwater_signal": evidence["allocator_highwater_signal"],
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()

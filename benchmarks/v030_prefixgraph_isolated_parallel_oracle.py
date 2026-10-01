from __future__ import annotations

"""Exact research A/B for restoring promoted PrefixGraph scheduling inside the isolated child.

Control is the current private canonical PrefixGraph builder at raw-prefix level 15.
Candidate uses the same private semantic owner and level but temporarily binds the
already-promoted bounded four-worker scheduler to that owner inside a fresh child.
The child still completes before any G04 construction.  This grants no release credit.
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

from benchmarks import v030_prefixgraph_parallel_anchor_oracle_v2 as TARGETS
from experiments import entropygraph_v030_prefixgraph as HIST
from experiments import entropygraph_v030_release_candidate as RC

EXPECTED_OWNER_MODULE = "experiments._v030_canonical_prefixgraph"
PREFIX_LEVEL = 15
PAIRS = 4
MIN_SHIFTED_RELATIVE = 0.20
MIN_SHIFTED_ABSOLUTE_S = 1.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _level15_codec(pg):
    def codec(prefix: bytes):
        dictionary = pg.zstd.ZstdCompressionDict(
            prefix, dict_type=pg.zstd.DICT_TYPE_RAWCONTENT
        )
        compressor = pg.zstd.ZstdCompressor(
            level=PREFIX_LEVEL, dict_data=dictionary
        )
        return compressor, dictionary
    return codec


def _child(mode: str, source: Path, archive: Path) -> None:
    # Keep all monkeypatching process-local, matching the shipping lifetime boundary.
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_prefixgraph_parallel as parallel

    pg = canonical.RC.PG
    isolation = canonical.PROFILE_ISOLATION
    if pg is not isolation.PG or pg.__name__ != EXPECTED_OWNER_MODULE:
        raise RuntimeError("private PrefixGraph semantic-owner drift")

    original_codec = pg._prefix_codec
    original_base = parallel.BASE
    pg._prefix_codec = _level15_codec(pg)
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    try:
        if mode == "serial":
            stats = dict(pg.build(source, archive))
        elif mode == "parallel":
            # Reuse the promoted scheduler rather than copying it.  Only its BASE
            # semantic owner changes, and only inside this short-lived child.
            parallel.BASE = pg
            stats = dict(parallel.build(source, archive))
        else:
            raise ValueError(mode)
    finally:
        parallel.BASE = original_base
        pg._prefix_codec = original_codec

    print(
        json.dumps(
            {
                "schema": "cmpct-v030-prefixgraph-isolated-parallel-child-v1",
                "mode": mode,
                "semantic_owner": pg.__name__,
                "prefix_level": PREFIX_LEVEL,
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": _sha256(archive),
                "build_wall_s": time.perf_counter() - started_wall,
                "build_cpu_s": time.process_time() - started_cpu,
                "maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "g04_constructed": False,
                "stats": stats,
            },
            separators=(",", ":"),
            default=str,
        ),
        flush=True,
    )


def _invoke(mode: str, source: Path, archive: Path) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        mode,
        "--source",
        str(source),
        "--archive",
        str(archive),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    process_wall = time.perf_counter() - started
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not lines:
        raise RuntimeError(
            f"{mode} child failed rc={completed.returncode}: "
            f"{completed.stderr[-4000:]}"
        )
    receipt = json.loads(lines[-1])
    receipt["process_wall_s"] = process_wall
    if receipt.get("semantic_owner") != EXPECTED_OWNER_MODULE:
        raise RuntimeError("child semantic-owner drift")
    if int(receipt.get("prefix_level", -1)) != PREFIX_LEVEL:
        raise RuntimeError("child prefix-level drift")
    if receipt.get("g04_constructed") is not False:
        raise RuntimeError("child-before-G04 lifetime drift")
    if int(receipt.get("archive_bytes", -1)) != archive.stat().st_size:
        raise RuntimeError("child archive-size accounting drift")
    if receipt.get("archive_sha256") != _sha256(archive):
        raise RuntimeError("child archive-SHA accounting drift")
    return receipt


def _logical_name(source: Path) -> str:
    for target in ("shifted_versions", "boundary_churn"):
        if source.name == target or source.name.endswith("_" + target):
            return target
    raise RuntimeError(f"unexpected target {source}")


def _measure(suite: str, source: Path, root: Path) -> dict:
    logical = _logical_name(source)
    expected_tree = RC.treehash(source)
    eligible, reject = RC._prefixgraph_eligibility(source, expected_tree)
    if not eligible:
        raise RuntimeError(f"{suite}/{source.name} ineligible: {reject}")

    pairs = []
    for pair_index in range(PAIRS):
        pair_root = root / logical / f"pair-{pair_index}"
        pair_root.mkdir(parents=True, exist_ok=True)
        order = (
            ("serial", "parallel")
            if pair_index % 2 == 0
            else ("parallel", "serial")
        )
        receipts = {}
        paths = {}
        for mode in order:
            archive = pair_root / f"{mode}.cmpct"
            receipts[mode] = _invoke(mode, source, archive)
            paths[mode] = archive

        control = receipts["serial"]
        candidate = receipts["parallel"]
        if (
            control["archive_bytes"],
            control["archive_sha256"],
        ) != (
            candidate["archive_bytes"],
            candidate["archive_sha256"],
        ):
            raise RuntimeError(f"{suite}/{source.name}: archive identity drift")

        cs = control["stats"]
        ns = candidate["stats"]
        for field in ("anchor", "anchor_auditions", "tree_sha256"):
            if cs.get(field) != ns.get(field):
                raise RuntimeError(
                    f"{suite}/{source.name}: {field} drift"
                )
        if cs.get("tree_sha256") != expected_tree:
            raise RuntimeError(f"{suite}/{source.name}: source tree drift")

        # Verification is outside the child build timer.
        for mode in ("serial", "parallel"):
            verified = HIST.strong_verify(paths[mode])
            if verified.get("tree_sha256") != expected_tree:
                raise RuntimeError(
                    f"{suite}/{source.name}: {mode} verification drift"
                )

        pairs.append(
            {
                "pair_index": pair_index,
                "order": list(order),
                "serial": control,
                "parallel": candidate,
                "rss_ratio": (
                    candidate["maxrss_kib"] / max(1, control["maxrss_kib"])
                ),
            }
        )

    serial_build = [p["serial"]["build_wall_s"] for p in pairs]
    parallel_build = [p["parallel"]["build_wall_s"] for p in pairs]
    serial_process = [p["serial"]["process_wall_s"] for p in pairs]
    parallel_process = [p["parallel"]["process_wall_s"] for p in pairs]
    med_serial_build = statistics.median(serial_build)
    med_parallel_build = statistics.median(parallel_build)
    med_serial_process = statistics.median(serial_process)
    med_parallel_process = statistics.median(parallel_process)
    build_saving = med_serial_build - med_parallel_build

    return {
        "logical_target": logical,
        "label": f"{suite}/{source.name}",
        "source_tree_sha256": expected_tree,
        "pairs": pairs,
        "median_serial_build_wall_s": med_serial_build,
        "median_parallel_build_wall_s": med_parallel_build,
        "median_build_wall_saving_s": build_saving,
        "median_build_wall_improvement": (
            build_saving / max(med_serial_build, 1e-12)
        ),
        "median_serial_process_wall_s": med_serial_process,
        "median_parallel_process_wall_s": med_parallel_process,
        "median_process_wall_saving_s": (
            med_serial_process - med_parallel_process
        ),
        "median_candidate_to_control_rss_ratio": statistics.median(
            p["rss_ratio"] for p in pairs
        ),
        "exact_archive_identity_all": True,
        "exact_tree_identity_all": True,
        "strong_verify_all": True,
        "child_before_g04_barrier_all": True,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    targets = TARGETS._find_targets(work_root / "corpus")
    rows = [
        _measure(suite, source, work_root / "runs")
        for suite, source in targets
    ]
    by_name = {row["logical_target"]: row for row in rows}
    shifted = by_name["shifted_versions"]
    boundary = by_name["boundary_churn"]
    gate = {
        "exact_target_count": len(rows) == 2,
        "four_pairs_each": all(len(row["pairs"]) == PAIRS for row in rows),
        "exact_archive_identity_all": all(
            row["exact_archive_identity_all"] for row in rows
        ),
        "exact_tree_identity_all": all(
            row["exact_tree_identity_all"] for row in rows
        ),
        "strong_verify_all": all(row["strong_verify_all"] for row in rows),
        "child_before_g04_barrier_all": all(
            row["child_before_g04_barrier_all"] for row in rows
        ),
        "shifted_relative_materiality": (
            shifted["median_build_wall_improvement"]
            >= MIN_SHIFTED_RELATIVE
        ),
        "shifted_absolute_materiality": (
            shifted["median_build_wall_saving_s"]
            >= MIN_SHIFTED_ABSOLUTE_S
        ),
        "boundary_non_regression": (
            boundary["median_build_wall_saving_s"] >= 0.0
        ),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-prefixgraph-isolated-parallel-oracle-v1",
        "release_credit": False,
        "pairs": PAIRS,
        "prefix_level": PREFIX_LEVEL,
        "rows": rows,
        "gate": gate,
        "decision_law": (
            "Any archive/tree/anchor/count/prefix-level/process-boundary drift "
            "kills the mechanism. Shifted must improve median child build wall "
            "by >=20% and >=1.0 s; Boundary Churn must not regress. Research "
            "green earns only full unchanged product runtime/RSS/external follow-up."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path(
            "benchmark-artifacts/v030-prefixgraph-isolated-parallel-work"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "benchmark-artifacts/v030-prefixgraph-isolated-parallel.json"
        ),
    )
    parser.add_argument("--child", choices=("serial", "parallel"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.source is None or args.archive is None:
            parser.error("--source and --archive are required in child mode")
        _child(args.child, args.source, args.archive)
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["rows"], "gate": result["gate"]}, indent=2))
    if not result["gate"]["passed"]:
        raise SystemExit(
            "isolated PrefixGraph parallel recomposition failed its preregistered court"
        )


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Portable 15-workload A/B for attempt-5 position-independent discovery.

Research-only causal oracle. It compares the unchanged accepted attempt-5 graph against the same
engine with only Placement._position_independent_candidates disabled. The goal is to test the exact
generalization requirement left by the Shifted survival result: whether the additional discovery source
changes accepted attempt-5 graph bytes anywhere on the inherited portable frontier.

This does NOT authorize global deletion. The historical mosaic mechanism suites intentionally contain
multi-root workloads for which position-independent discovery was introduced and must remain a hostile
control before any shipping edit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from benchmarks import mosaic_v029_generalization_bench as GENERAL

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("baseline", "inherited-only")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _worker(kind: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    placement = accepted.BASE.P
    original = placement._position_independent_candidates

    def no_additional_discovery(sketches, nodes):
        return []

    if kind == "inherited-only":
        placement._position_independent_candidates = no_additional_discovery
    elif kind != "baseline":
        raise ValueError(kind)

    started = time.perf_counter()
    try:
        stats = accepted.build_graph(source, archive)
    finally:
        wall_s = time.perf_counter() - started
        placement._position_independent_candidates = original

    verified = dict(accepted.strong_verify(archive))
    return {
        "kind": kind,
        "wall_s": wall_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "verify_ok": bool(verified.get("ok")),
        "tree_sha256": verified.get("tree_sha256"),
        "mosaic_nodes": int(stats.get("mosaic_nodes", 0)),
        "mosaic_discovery_auditions": int(stats.get("mosaic_discovery_auditions", 0)),
        "residual_pack_records": int(stats.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(stats.get("residual_packed_delta_nodes", 0)),
    }


def _fresh(kind: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            __file__,
            "--worker",
            kind,
            "--source",
            os.fspath(source),
            "--archive",
            os.fspath(archive),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        raise RuntimeError(
            f"fresh discovery-generalization worker failed kind={kind} rc={proc.returncode} "
            f"stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}"
        )
    return json.loads(lines[-1])


def _build_corpora(work_root: Path) -> tuple[dict[tuple[str, str], Path], dict[tuple[str, str], dict]]:
    preserved = GENERAL._preserved_rows()
    neutral = GENERAL._load(
        ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_discovery_general_neutral",
    )
    hostile = GENERAL._load(
        ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_discovery_general_hostile",
    )
    repair = GENERAL._load(
        GENERAL.REPAIR_PATH,
        "cmpct_v030_discovery_general_repair",
    )
    repair.install_generation_hooks(neutral)

    neutral_root = work_root / "neutral"
    hostile_root = work_root / "resemblance"
    neutral.build(neutral_root)
    repair.normalize_root(neutral_root)
    hostile.build(hostile_root)

    roots = {}
    for suite, root in (
        ("neutral_hostile_v1", neutral_root),
        ("resemblance_hostile_v1", hostile_root),
    ):
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            if key not in preserved:
                raise RuntimeError(f"unexpected workload {key}")
            roots[key] = workload

    if set(roots) != set(preserved):
        missing = sorted(set(preserved) - set(roots))
        extra = sorted(set(roots) - set(preserved))
        raise RuntimeError(f"portable frontier mismatch missing={missing} extra={extra}")
    return roots, preserved


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots, preserved = _build_corpora(work_root)
    rows = []
    invalid = []

    for index, key in enumerate(sorted(roots)):
        suite, name = key
        source = roots[key]
        expected_tree = str(preserved[key]["tree_sha256"])
        got_tree = GENERAL.ENGINE.BASE.treehash(source)
        if got_tree != expected_tree:
            raise RuntimeError(f"portable source drift for {key}: {got_tree} != {expected_tree}")

        order = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
        measured = {}
        for kind in order:
            archive = work_root / "archives" / f"{suite}-{name}-{kind}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            measured[kind] = _fresh(kind, source, archive)

        for kind in ARMS:
            item = measured[kind]
            if item["verify_ok"] is not True:
                invalid.append(f"{suite}/{name}:{kind}:verify")
            if item["tree_sha256"] != expected_tree:
                invalid.append(f"{suite}/{name}:{kind}:tree")

        same_bytes = int(measured["baseline"]["archive_bytes"]) == int(
            measured["inherited-only"]["archive_bytes"]
        )
        same_sha = measured["baseline"]["archive_sha256"] == measured["inherited-only"]["archive_sha256"]
        rows.append(
            {
                "suite": suite,
                "name": name,
                "tree_sha256": expected_tree,
                "execution_order": list(order),
                "baseline": measured["baseline"],
                "inherited_only": measured["inherited-only"],
                "byte_delta": int(measured["inherited-only"]["archive_bytes"])
                - int(measured["baseline"]["archive_bytes"]),
                "byte_identical": same_bytes and same_sha,
            }
        )
        print(
            json.dumps(
                {
                    "suite": suite,
                    "name": name,
                    "byte_delta": rows[-1]["byte_delta"],
                    "byte_identical": rows[-1]["byte_identical"],
                    "baseline_mosaic_nodes": measured["baseline"]["mosaic_nodes"],
                    "baseline_discovery_auditions": measured["baseline"]["mosaic_discovery_auditions"],
                },
                separators=(",", ":"),
            ),
            flush=True,
        )

    changed = [row for row in rows if not row["byte_identical"]]
    if invalid:
        decision = "INVALID"
    elif changed:
        decision = "DISCOVERY_SOURCE_SIZE_CONTRIBUTING_ON_PORTABLE_15"
    else:
        decision = "DISCOVERY_SOURCE_BYTE_DEAD_ON_PORTABLE_15"

    return {
        "schema": "cmpct-v030-g04-discovery-generalization-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "rows": rows,
        "decision": decision,
        "invalid_reasons": invalid,
        "summary": {
            "workloads": len(rows),
            "byte_identical_rows": sum(row["byte_identical"] for row in rows),
            "changed_rows": [f"{row['suite']}/{row['name']}" for row in changed],
            "baseline_mosaic_nodes": sum(row["baseline"]["mosaic_nodes"] for row in rows),
            "baseline_discovery_auditions": sum(
                row["baseline"]["mosaic_discovery_auditions"] for row in rows
            ),
            "baseline_wall_s": sum(float(row["baseline"]["wall_s"]) for row in rows),
            "inherited_only_wall_s": sum(float(row["inherited_only"]["wall_s"]) for row in rows),
        },
        "contract": {
            "portable_workloads": 15,
            "single_ablation": "accepted.BASE.P._position_independent_candidates -> []",
            "same_source_tree_per_pair": True,
            "exact_graph_bytes_and_sha_decide": True,
            "timing_supporting_only": True,
            "product_changed": False,
            "release_credit": False,
            "global_deletion_authorized": False,
            "required_global_negative_control": "historical 18-workload mosaic mechanism gate",
        },
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=ARMS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()

    if args.worker:
        print(json.dumps(_worker(args.worker, args.source, args.archive), separators=(",", ":")))
        return

    if args.work_root is None or args.output is None:
        parser.error("--work-root and --output are required outside --worker")

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "summary": result["summary"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()

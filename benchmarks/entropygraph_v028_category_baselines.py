from __future__ import annotations

"""Measure public v0.28 workload categories against ZIP/Deflate and solid Zstandard.

This is a presentation-evidence companion to the causal EntropyGraph-II benchmark. It does not rerun
or rescore CMPCT. Instead, it regenerates the deterministic public workload trees, verifies their exact
identity against a freshly-produced v0.28 frontier record, and measures two lightweight external size
baselines on each identical tree.

Footnote: the resulting per-workload totals are *independent-archive* measurements and therefore must
not replace the whole-suite structural arena on the homepage. Their purpose is narrower: answer the
category question "where does current CMPCT beat or lose to a serious Zstandard size baseline?" while
retaining ZIP/Deflate as a familiar secondary baseline and keeping the canonical ZIP execution table
semantically separate.
"""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE_BENCH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _pct_smaller(candidate: int, baseline: int) -> float | None:
    if baseline <= 0:
        return None
    return (baseline - candidate) / baseline * 100.0


def _measure_suite(base, corpus_path: Path, module_name: str, suite_name: str,
                   frontier_rows: dict[tuple[str, str], dict], temp: Path) -> list[dict]:
    corpus = _load(corpus_path, module_name)
    suite_root = temp / suite_name
    corpus.build(suite_root)
    out: list[dict] = []

    for workload in sorted(p for p in suite_root.iterdir() if p.is_dir()):
        key = (suite_name, workload.name)
        source = frontier_rows.get(key)
        if source is None:
            raise SystemExit(f"frontier record is missing deterministic workload {suite_name}/{workload.name}")

        files, logical, tree_sha256 = base._tree_stats(workload)
        expected_tree = str(source.get("tree_sha256") or "")
        if tree_sha256 != expected_tree:
            raise SystemExit(
                f"tree identity drift for {suite_name}/{workload.name}: {tree_sha256} != {expected_tree}"
            )
        if files != int(source.get("files") or 0) or logical != int(source.get("logical_bytes") or 0):
            raise SystemExit(f"tree accounting drift for {suite_name}/{workload.name}")

        with tempfile.TemporaryDirectory(prefix="cmpct-v028-category-") as td:
            row_temp = Path(td)
            zip_row = base._zip_deflate(workload, row_temp / "out.zip")
            zstd_row = base._solid_tar_zstd(workload, row_temp / "out.tar.zst")

        if not zip_row.get("available"):
            raise SystemExit(f"ZIP/Deflate baseline unavailable for {suite_name}/{workload.name}")
        if not zstd_row.get("available"):
            raise SystemExit(
                f"solid tar/Zstandard baseline unavailable for {suite_name}/{workload.name}: "
                f"{zstd_row.get('reason', 'unknown reason')}"
            )

        candidate = int(source.get("candidate_bytes") or 0)
        zip_bytes = int(zip_row["bytes"])
        zstd_bytes = int(zstd_row["bytes"])
        out.append(
            {
                "suite": suite_name,
                "name": workload.name,
                "files": files,
                "logical_bytes": logical,
                "tree_sha256": tree_sha256,
                "cmpct_bytes": candidate,
                "zip_deflate9_bytes": zip_bytes,
                "tar_zstd19_solid_bytes": zstd_bytes,
                "cmpct_vs_zip_deflate9_pct": _pct_smaller(candidate, zip_bytes),
                "cmpct_vs_tar_zstd19_pct": _pct_smaller(candidate, zstd_bytes),
            }
        )
        print(
            json.dumps(
                {
                    "suite": suite_name,
                    "name": workload.name,
                    "cmpct": candidate,
                    "zip_deflate9": zip_bytes,
                    "tar_zstd19_solid": zstd_bytes,
                }
            ),
            flush=True,
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontier", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    frontier = json.loads(args.frontier.read_text(encoding="utf-8"))
    frontier_rows = {
        (str(row.get("suite") or ""), str(row.get("name") or "")): row
        for row in list(frontier.get("rows") or [])
    }
    if not frontier_rows:
        raise SystemExit("frontier record contains no workload rows")

    base = _load(BASE_BENCH, "entropygraph_v028_category_base")
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="cmpct-v028-category-corpora-") as td:
        temp = Path(td)
        rows += _measure_suite(
            base,
            ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
            "cmpct_category_neutral_v1",
            "neutral_hostile_v1",
            frontier_rows,
            temp,
        )
        rows += _measure_suite(
            base,
            ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
            "cmpct_category_hostile_v1",
            "resemblance_hostile_v1",
            frontier_rows,
            temp,
        )

    candidate_total = sum(int(row["cmpct_bytes"]) for row in rows)
    zip_total = sum(int(row["zip_deflate9_bytes"]) for row in rows)
    zstd_total = sum(int(row["tar_zstd19_solid_bytes"]) for row in rows)
    record = {
        "schema": "cmpct-entropygraph-v028-category-baselines-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project_version": frontier.get("candidate", {}).get("project_version")
        or frontier.get("project_version")
        or "0.28.0",
        "source_frontier": args.frontier.name,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "zstd": shutil.which("zstd"),
        },
        "contract": {
            "aggregation": "each deterministic workload is archived independently",
            "cmpct_source": "candidate_bytes copied from the freshly-produced strict v0.28 frontier after exact tree identity verification",
            "zip_baseline": "deterministic ZIP/Deflate-9 from Python zipfile",
            "zstd_baseline": "deterministic tar stream compressed with Zstandard-19, single thread",
            "semantic_note": "solid tar+Zstd is a size baseline with materially different selective-access and recovery semantics",
            "intended_surface": "per-category public matrix; not the whole-suite structural arena and not canonical ZIP execution parity",
        },
        "rows": rows,
        "totals": {
            "workloads": len(rows),
            "candidate_bytes": candidate_total,
            "zip_deflate9_bytes": zip_total,
            "tar_zstd19_solid_bytes": zstd_total,
            "cmpct_smaller_than_zip_deflate9_pct": _pct_smaller(candidate_total, zip_total),
            "cmpct_smaller_than_tar_zstd19_pct": _pct_smaller(candidate_total, zstd_total),
            "wins_vs_zip_deflate9": sum(row["cmpct_bytes"] < row["zip_deflate9_bytes"] for row in rows),
            "wins_vs_tar_zstd19": sum(row["cmpct_bytes"] < row["tar_zstd19_solid_bytes"] for row in rows),
            "losses_vs_tar_zstd19": sum(row["cmpct_bytes"] > row["tar_zstd19_solid_bytes"] for row in rows),
            "ties_vs_tar_zstd19": sum(row["cmpct_bytes"] == row["tar_zstd19_solid_bytes"] for row in rows),
        },
    }

    # Footnote: fail closed if the companion measurement did not cover the exact same workload set.
    # A partial category matrix would selectively hide losses and is not acceptable public evidence.
    if len(rows) != len(frontier_rows):
        raise SystemExit(f"category baseline covered {len(rows)} rows but frontier contains {len(frontier_rows)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["totals"], indent=2), flush=True)


if __name__ == "__main__":
    main()

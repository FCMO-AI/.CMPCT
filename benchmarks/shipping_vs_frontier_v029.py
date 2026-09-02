#!/usr/bin/env python3
from __future__ import annotations

"""Exact-tree v0.29 shipping-vs-frontier storage benchmark.

This benchmark answers one deliberately narrow question: on the same 15 public v0.29 workload trees,
how many stored bytes does the shipping canonical revision-24 writer produce versus the accepted v0.29
Mosaic / Residual Program Packing research frontier?

It does not claim semantic parity between the two authority levels. Canonical r24 is the interoperable
reader/writer contract; the frontier may emit CMPNX11 or an inherited research fallback. Each workload
is archived independently, so these totals are also intentionally separate from the whole-suite
structural arena where cross-workload context can change the result.

Archive size is deterministic for an identical live tree and encoder policy. Timing is intentionally not
mixed into this record: a same-runner repeated timing study should be a separate benchmark with its own
noise model rather than turning deterministic storage evidence into a weaker composite claim.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

from cmpct.builder import Builder
from cmpct.reader import CMPCT

import mosaic_v029_generalization_bench as general


def _source_for(work_root: Path, suite: str, name: str) -> Path:
    if suite == "neutral_hostile_v1":
        return work_root / "neutral" / name
    if suite == "resemblance_hostile_v1":
        return work_root / "resemblance" / name
    raise ValueError(f"unknown suite: {suite}")


def _canonical_size_and_verify(source: Path, out: Path, restore: Path) -> tuple[int, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    shutil.rmtree(restore, ignore_errors=True)

    Builder(source).build(out)
    first_size = out.stat().st_size

    # Deterministic-size sanity check: rebuild the exact same tree and require the byte count to match.
    out2 = out.with_suffix(out.suffix + ".repeat")
    out2.unlink(missing_ok=True)
    Builder(source).build(out2)
    second_size = out2.stat().st_size
    out2.unlink(missing_ok=True)
    if first_size != second_size:
        raise RuntimeError(
            f"canonical archive size was not deterministic for {source}: {first_size} != {second_size}"
        )

    with CMPCT(out) as archive:
        verified_members = int(archive.verify())
        archive.extractall(restore, metadata=True)

    expected_tree = general.ENGINE.BASE.treehash(source)
    restored_tree = general.ENGINE.BASE.treehash(restore)
    if restored_tree != expected_tree:
        raise RuntimeError(
            f"canonical round-trip tree hash mismatch for {source}: {restored_tree} != {expected_tree}"
        )
    return first_size, verified_members


def run(work_root: Path) -> dict:
    frontier = general.run(work_root, with_category_baselines=False)
    rows = []
    shipping_root = work_root / "shipping-vs-frontier"

    for source_row in frontier["rows"]:
        suite = source_row["suite"]
        name = source_row["name"]
        source = _source_for(work_root, suite, name)
        shipping_archive = shipping_root / "archives" / suite / f"{name}.cmpct"
        restore = shipping_root / "restored" / suite / name
        shipping_bytes, verified_members = _canonical_size_and_verify(source, shipping_archive, restore)
        frontier_bytes = int(source_row["candidate_bytes"])
        delta = shipping_bytes - frontier_bytes
        rows.append(
            {
                "suite": suite,
                "name": name,
                "files": int(source_row["files"]),
                "logical_bytes": int(source_row["logical_bytes"]),
                "tree_sha256": source_row["tree_sha256"],
                "shipping_format_revision": 24,
                "shipping_bytes": shipping_bytes,
                "shipping_verified_members": verified_members,
                "frontier_identity": "v0.29 accepted Mosaic / Residual Program Packing",
                "frontier_selected": source_row["selected"],
                "frontier_bytes": frontier_bytes,
                "frontier_saving_bytes": delta,
                "frontier_smaller_than_shipping_pct": delta / shipping_bytes * 100.0 if shipping_bytes else 0.0,
            }
        )
        print(
            json.dumps(
                {
                    "suite": suite,
                    "name": name,
                    "shipping_bytes": shipping_bytes,
                    "frontier_bytes": frontier_bytes,
                    "frontier_saving_bytes": delta,
                }
            ),
            flush=True,
        )

    shipping_total = sum(row["shipping_bytes"] for row in rows)
    frontier_total = sum(row["frontier_bytes"] for row in rows)
    delta_total = shipping_total - frontier_total
    totals = {
        "workloads": len(rows),
        "files": sum(row["files"] for row in rows),
        "logical_bytes": sum(row["logical_bytes"] for row in rows),
        "shipping_bytes": shipping_total,
        "frontier_bytes": frontier_total,
        "frontier_saving_bytes": delta_total,
        "frontier_smaller_than_shipping_pct": (
            delta_total / shipping_total * 100.0 if shipping_total else 0.0
        ),
        "frontier_wins": sum(row["frontier_bytes"] < row["shipping_bytes"] for row in rows),
        "shipping_wins": sum(row["shipping_bytes"] < row["frontier_bytes"] for row in rows),
        "ties": sum(row["shipping_bytes"] == row["frontier_bytes"] for row in rows),
    }
    if totals["workloads"] != 15:
        raise RuntimeError(f"expected 15 public workloads, measured {totals['workloads']}")

    return {
        "schema": "cmpct-v029-shipping-vs-frontier-v1",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "project_version": "0.29.0",
        "shipping": {
            "authority": "canonical reader/writer",
            "format_revision": 24,
            "engine": "src/cmpct/ Builder/CMPCT",
            "meaning": "interoperable shipping contract",
        },
        "frontier": {
            "authority": "research frontier",
            "engine": "accepted v0.29 Mosaic / Residual Program Packing",
            "grammar": "CMPNX11 or inherited research fallback",
            "meaning": "experimental representation; not canonical-r24 syntax",
        },
        "benchmark_contract": {
            "question": "stored bytes: shipping canonical r24 versus accepted v0.29 research frontier",
            "aggregation": "each of the 15 public v0.29 workloads archived independently",
            "same_lifetime_measurement": True,
            "same_tree_per_row": True,
            "shipping_size_repeat_check": 2,
            "frontier_verification": "strong_verify performed by inherited v0.29 generalization gate",
            "shipping_verification": "canonical verify plus extract-and-treehash round trip",
            "timing_claim": None,
            "semantic_qualification": (
                "This is a same-tree storage comparison between two CMPCT authority levels, not an "
                "interoperability or feature-parity claim. The frontier is not readable as canonical r24."
            ),
        },
        "frontier_source": {
            "schema": frontier.get("schema"),
            "engine": frontier.get("engine"),
            "preserved_baselines": frontier.get("preserved_baselines"),
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Shipping_vs_Frontier"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(json.dumps(result["totals"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

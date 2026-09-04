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

The synthetic corpus generators can assign wall-clock mtimes even when file bytes are deterministic.
Canonical r24 preserves those timestamps, while the research tree hash intentionally identifies content
and structure rather than host-time metadata. Therefore this benchmark normalizes every generated path
mtime to the Unix epoch *before either encoder sees the tree*. It does not enable Builder reproducible
mode: shipping still uses the ordinary fidelity-preserving canonical encoder on a deterministic source.

Archive size is deterministic for an identical live tree and encoder policy. Timing is intentionally not
mixed into this record: a same-runner repeated timing study should be a separate benchmark with its own
noise model rather than turning deterministic storage evidence into a weaker composite claim.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from cmpct.builder import Builder
from cmpct.reader import CMPCT

import mosaic_v029_generalization_bench as general


ACCEPTED_FRONTIER = general.ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-public.json"
NORMALIZED_MTIME_NS = 0


def _checked_out_commit() -> str | None:
    """Return the commit whose files are actually being benchmarked."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return os.environ.get("GITHUB_SHA")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _accepted_rows() -> tuple[dict[tuple[str, str], dict], dict]:
    record = json.loads(ACCEPTED_FRONTIER.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-public-mosaic-v029-benchmark-v1":
        raise RuntimeError("accepted v0.29 public frontier record has an unexpected schema")
    portable = record.get("portable_frontier") or {}
    rows = portable.get("rows") or []
    if len(rows) != 15:
        raise RuntimeError(f"accepted v0.29 public frontier must contain 15 rows, found {len(rows)}")
    keyed = {(row["suite"], row["name"]): row for row in rows}
    if len(keyed) != 15:
        raise RuntimeError("accepted v0.29 public frontier contains duplicate workload identities")
    return keyed, record


def _normalize_tree_mtimes(root: Path) -> None:
    """Freeze generated path mtimes so canonical metadata bytes are cross-run comparable.

    The normalization applies to files, directories and symlinks. Fail closed if a path cannot be
    normalized or reports a non-zero nanosecond mtime afterwards; silently accepting host timestamps
    would recreate the benchmark drift this gate exists to prevent.
    """
    paths = list(root.rglob("*"))
    # Children first keeps directory mtimes at the normalized value after touching descendants.
    for path in sorted(paths, key=lambda p: len(p.parts), reverse=True):
        try:
            os.utime(path, ns=(NORMALIZED_MTIME_NS, NORMALIZED_MTIME_NS), follow_symlinks=False)
        except (NotImplementedError, OSError) as exc:
            raise RuntimeError(f"could not normalize mtime for {path}") from exc
    try:
        os.utime(root, ns=(NORMALIZED_MTIME_NS, NORMALIZED_MTIME_NS), follow_symlinks=False)
    except (NotImplementedError, OSError) as exc:
        raise RuntimeError(f"could not normalize mtime for root {root}") from exc

    for path in [root, *paths]:
        if path.lstat().st_mtime_ns != NORMALIZED_MTIME_NS:
            raise RuntimeError(f"mtime normalization did not stick for {path}: {path.lstat().st_mtime_ns}")


def _canonical_size_and_verify(source: Path, out: Path, restore: Path) -> tuple[int, int, str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    shutil.rmtree(restore, ignore_errors=True)

    Builder(source).build(out)
    first_size = out.stat().st_size
    first_sha256 = _sha256_file(out)

    # Require byte-identical canonical output, not merely equal archive length.
    out2 = out.with_suffix(out.suffix + ".repeat")
    out2.unlink(missing_ok=True)
    Builder(source).build(out2)
    second_size = out2.stat().st_size
    second_sha256 = _sha256_file(out2)
    out2.unlink(missing_ok=True)
    if first_size != second_size or first_sha256 != second_sha256:
        raise RuntimeError(
            f"canonical archive was not byte-identical for {source}: "
            f"{first_size}/{first_sha256} != {second_size}/{second_sha256}"
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
    return first_size, verified_members, first_sha256


def _generate_and_measure_frontier(work_root: Path) -> list[dict]:
    """Generate each accepted public workload once, normalize it, then run the accepted frontier."""
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    preserved = general._preserved_rows()
    accepted, _ = _accepted_rows()

    neutral = general._load(
        general.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_shipping_frontier_neutral_v1",
    )
    hostile = general._load(
        general.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_shipping_frontier_hostile_v1",
    )
    repair = general._load(general.REPAIR_PATH, "cmpct_shipping_frontier_repair_v5")
    repair.install_generation_hooks(neutral)

    rows: list[dict] = []
    suites = [
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ]
    for label, builder, root in suites:
        builder.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        _normalize_tree_mtimes(root)

        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            row = general._measure_workload(
                label,
                workload,
                work_root / "frontier-archives" / label,
                preserved,
                with_category_baselines=False,
            )
            key = (label, workload.name)
            expected = accepted.get(key)
            if expected is None:
                raise RuntimeError(f"workload {label}/{workload.name} is absent from accepted v0.29 frontier")
            if not row["baseline_tree_match"] or not row["baseline_bytes_match"]:
                raise RuntimeError(f"inherited v0.28 identity drifted for {label}/{workload.name}")
            if row["tree_sha256"] != expected["tree_sha256"]:
                raise RuntimeError(
                    f"accepted tree identity drift for {label}/{workload.name}: "
                    f"{row['tree_sha256']} != {expected['tree_sha256']}"
                )
            if int(row["candidate_bytes"]) != int(expected["candidate_bytes"]):
                raise RuntimeError(
                    f"accepted frontier bytes drift for {label}/{workload.name}: "
                    f"{row['candidate_bytes']} != {expected['candidate_bytes']}"
                )
            if row["selected"] != expected["selected"]:
                raise RuntimeError(
                    f"accepted frontier selection drift for {label}/{workload.name}: "
                    f"{row['selected']} != {expected['selected']}"
                )
            rows.append(row)
            print(
                json.dumps(
                    {
                        "suite": label,
                        "name": workload.name,
                        "tree_sha256": row["tree_sha256"],
                        "frontier_bytes": row["candidate_bytes"],
                        "frontier_selected": row["selected"],
                        "accepted_frontier_match": True,
                    }
                ),
                flush=True,
            )
    return rows


def _source_for(work_root: Path, suite: str, name: str) -> Path:
    if suite == "neutral_hostile_v1":
        return work_root / "neutral" / name
    if suite == "resemblance_hostile_v1":
        return work_root / "resemblance" / name
    raise ValueError(f"unknown suite: {suite}")


def run(work_root: Path) -> dict:
    frontier_rows = _generate_and_measure_frontier(work_root)
    accepted_rows, accepted_record = _accepted_rows()
    rows = []
    shipping_root = work_root / "shipping-vs-frontier"

    for source_row in frontier_rows:
        suite = source_row["suite"]
        name = source_row["name"]
        source = _source_for(work_root, suite, name)
        # Defensive check: generation/measurement must not have reintroduced timestamp drift.
        for path in [source, *source.rglob("*")]:
            if path.lstat().st_mtime_ns != NORMALIZED_MTIME_NS:
                raise RuntimeError(f"mtime drifted before canonical measurement: {path}")

        shipping_archive = shipping_root / "archives" / suite / f"{name}.cmpct"
        restore = shipping_root / "restored" / suite / name
        shipping_bytes, verified_members, shipping_sha256 = _canonical_size_and_verify(
            source, shipping_archive, restore
        )
        accepted = accepted_rows[(suite, name)]
        frontier_bytes = int(accepted["candidate_bytes"])
        delta = shipping_bytes - frontier_bytes
        rows.append(
            {
                "suite": suite,
                "name": name,
                "files": int(source_row["files"]),
                "logical_bytes": int(source_row["logical_bytes"]),
                "tree_sha256": source_row["tree_sha256"],
                "source_mtime_ns": NORMALIZED_MTIME_NS,
                "shipping_format_revision": 24,
                "shipping_bytes": shipping_bytes,
                "shipping_sha256": shipping_sha256,
                "shipping_verified_members": verified_members,
                "frontier_identity": "v0.29 accepted Mosaic / Residual Program Packing",
                "frontier_selected": accepted["selected"],
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
                    "shipping_sha256": shipping_sha256,
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

    accepted_portable = accepted_record.get("portable_frontier") or {}
    if frontier_total != int(accepted_portable.get("candidate_bytes", -1)):
        raise RuntimeError(
            f"frontier aggregate no longer matches accepted v0.29 public record: "
            f"{frontier_total} != {accepted_portable.get('candidate_bytes')}"
        )

    return {
        "schema": "cmpct-v029-shipping-vs-frontier-v1",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "source_commit": _checked_out_commit(),
        "project_version": "0.29.0",
        "shipping": {
            "authority": "canonical reader/writer",
            "format_revision": 24,
            "engine": "src/cmpct/ Builder/CMPCT",
            "mode": "default fidelity-preserving encoder on normalized synthetic source metadata",
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
            "source_metadata_normalization": "all generated path mtimes normalized to Unix epoch before either encoder",
            "source_mtime_ns": NORMALIZED_MTIME_NS,
            "shipping_byte_identical_repeat_check": 2,
            "frontier_acceptance_lock": "benchmarks/history/2026-08-17-mosaic-v029-public.json",
            "frontier_verification": "strong_verify plus exact accepted tree/bytes/selection lock per workload",
            "shipping_verification": "canonical verify plus extract-and-treehash round trip plus byte-identical repeat archive",
            "timing_claim": None,
            "semantic_qualification": (
                "This is a same-tree storage comparison between two CMPCT authority levels, not an "
                "interoperability or feature-parity claim. The frontier is not readable as canonical r24."
            ),
        },
        "frontier_source": {
            "schema": accepted_record.get("schema"),
            "record": "benchmarks/history/2026-08-17-mosaic-v029-public.json",
            "candidate": accepted_record.get("candidate") or {},
            "candidate_bytes": int(accepted_portable["candidate_bytes"]),
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

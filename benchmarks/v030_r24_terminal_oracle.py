from __future__ import annotations

"""Prove the verified terminal-r24 envelope before skipping speculative r25 construction.

The exact-r24 wide-chunk oracle found a strict size/create Pareto win for the frozen single-large-file workload,
but its ``create_s`` intentionally stopped before strong verification.  A release-product terminal path would have
to return only after mandatory selected-artifact verification.  This oracle measures that complete boundary:

    source-shape scan + release-r24 build + strong verification

against deterministic ZIP/Deflate-9 and solid tar+Zstd-19, while also requiring the completed r24 artifact to be
strictly smaller than the accepted v0.29 row.  Only the structurally admitted envelope (exactly one regular file,
largest >=8 MiB) is evaluated.  No result changes shipping selection by itself.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT

MIN_BYTES = PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES


def _shape(root: Path) -> tuple[int, int]:
    count = largest = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            st = os.lstat(Path(dirpath) / name)
            if stat.S_ISREG(st.st_mode):
                count += 1
                largest = max(largest, int(st.st_size))
    return count, largest


def _one(label: str, source: Path, accepted_v029_bytes: int, work: Path) -> dict:
    count, largest = _shape(source)
    eligible = count == 1 and largest >= MIN_BYTES
    row = {
        "label": label,
        "regular_files": count,
        "largest_regular_file_bytes": largest,
        "eligible": eligible,
    }
    if not eligible:
        return row
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-terminal-r24-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        expected_tree = B._tree(source)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "zstd")

        archive = root / "terminal-r24.cmpct"
        started = time.perf_counter()
        build_stats = PRODUCT._locality_bounded_r24_build(stage, archive)
        verified = PRODUCT.strong_verify(archive)
        complete_create_s = time.perf_counter() - started
        if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
            raise RuntimeError(f"terminal r24 failed strong verification: {verified!r}")
        if verified.get("tree_sha256") != expected_tree:
            raise RuntimeError("terminal r24 source tree mismatch")

        archive_bytes = archive.stat().st_size
        gate = {
            "strictly_smaller_than_v029": archive_bytes < accepted_v029_bytes,
            "strictly_smaller_than_zip": archive_bytes < int(zip_result["archive_bytes"]),
            "strictly_smaller_than_zstd19": archive_bytes < int(zstd_result["archive_bytes"]),
            "strictly_faster_than_zip": complete_create_s < float(zip_result["create_s"]),
            "strictly_faster_than_zstd19": complete_create_s < float(zstd_result["create_s"]),
            "strong_verify_green": True,
            "wide_policy_selected": build_stats.get("large_file_chunk_policy") == "fixed-8mib",
        }
        gate["passed"] = all(gate.values())
        row.update({
            "accepted_v029_bytes": accepted_v029_bytes,
            "archive_bytes": archive_bytes,
            "complete_create_s": complete_create_s,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "build_stats": build_stats,
            "strong_verify": verified,
            "gate": gate,
        })
        return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_terminal_r24_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_terminal_r24_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_terminal_r24_repair")
    repair.install_generation_hooks(neutral)
    rows = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = accepted[key]
            if B._tree(workload) != expected["tree_sha256"]:
                raise RuntimeError(f"terminal-r24 source drift: {suite}/{workload.name}")
            row = _one(
                f"{suite}/{workload.name}",
                workload,
                int(expected["accepted_v029_bytes"]),
                work_root,
            )
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            if row["eligible"]:
                print(json.dumps({
                    "label": row["label"],
                    "bytes": row["archive_bytes"],
                    "create_s": row["complete_create_s"],
                    "v029": row["accepted_v029_bytes"],
                    "zip": [row["zip"]["archive_bytes"], row["zip"]["create_s"]],
                    "zstd": [row["tar_zstd19"]["archive_bytes"], row["tar_zstd19"]["create_s"]],
                    "gate": row["gate"],
                }, separators=(",", ":")), flush=True)
    eligible = [row for row in rows if row["eligible"]]
    return {
        "schema": "cmpct-v030-r24-terminal-oracle-v1",
        "claim_boundary": "research admission proof; shipping terminal selection remains unchanged",
        "admission": "exactly-one-regular-file-and-largest-ge-8mib",
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "eligible_workloads": len(eligible),
            "eligible_labels": [row["label"] for row in eligible],
            "all_eligible_pass": bool(eligible) and all(row["gate"]["passed"] for row in eligible),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-terminal-r24-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-terminal-r24.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)
    if not result["summary"]["all_eligible_pass"]:
        raise SystemExit("verified terminal-r24 envelope did not earn admission")


if __name__ == "__main__":
    main()

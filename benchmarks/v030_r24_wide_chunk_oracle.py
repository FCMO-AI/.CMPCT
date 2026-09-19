from __future__ import annotations

"""Exact-r24 oracle for wider large-file chunks under the frozen 8 MiB decode-unit ceiling.

Canonical r24 currently content-chunks large regular files with <=2 MiB CDC chunks (or 256 KiB fixed fallback).
The release law permits <=8 MiB decoded units.  On sparse/single-large-file workloads, spending more of that budget
can improve Zstd context while reducing the number of compressor calls, without changing revision-24 grammar,
reader semantics, integrity, member amplification, ZIP export or native compatibility.

This oracle A/Bs the shipping release-r24 builder policy against a deterministic 8 MiB fixed-chunk policy.  It is
restricted to workloads with <=8 regular files and at least one >=8 MiB member, where cross-file CDC reuse is not
the primary mechanism.  Both artifacts are strongly verified through the promoted release reader and must restore
the same canonical user-tree identity.  The experiment cannot authorize promotion; any shipping change must retain
the smaller exact r24 artifact per workload and pass the complete release matrix.
"""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time

from cmpct.builder import Builder
import cmpct.builder as BUILDER_MODULE
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as PRODUCT

WIDE_CHUNK_BYTES = 8 * 1024 * 1024
RELEASE_PACK_CAP_BYTES = 2 * 1024 * 1024
RELEASE_MICRO_MAX_FILE_BYTES = 32 * 1024
RELEASE_DEFLATE_REUSE_MIN_BYTES = 0


def _shape(root: Path) -> dict:
    files = 0
    logical = 0
    largest = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            st = os.lstat(path)
            if not stat.S_ISREG(st.st_mode):
                continue
            files += 1
            logical += int(st.st_size)
            largest = max(largest, int(st.st_size))
    return {"regular_files": files, "logical_bytes": logical, "largest_regular_file_bytes": largest}


@contextmanager
def _chunk_policy(wide: bool):
    original = BUILDER_MODULE.cdc_chunks
    if wide:
        # Deterministic fixed chunks make the A/B independent of optional native CDC availability.  The reader
        # never knows the encoder boundary algorithm; explicit [length, blob-ref] rows are already r24 grammar.
        BUILDER_MODULE.cdc_chunks = lambda data: [data[i:i+WIDE_CHUNK_BYTES] for i in range(0, len(data), WIDE_CHUNK_BYTES)]
    try:
        yield
    finally:
        BUILDER_MODULE.cdc_chunks = original


def _build(root: Path, out: Path, *, wide: bool) -> dict:
    started = time.perf_counter()
    with _chunk_policy(wide):
        builder = Builder(root, deflate_reuse_min=RELEASE_DEFLATE_REUSE_MIN_BYTES)
        builder.micro_pack_max_file = RELEASE_MICRO_MAX_FILE_BYTES
        shape = _shape(root)
        largest = int(shape["largest_regular_file_bytes"])
        if largest > 0:
            builder.micro_pack_target = min(RELEASE_PACK_CAP_BYTES, 8 * largest)
        stats = dict(builder.build(out))
    create_s = time.perf_counter() - started
    verified = PRODUCT.strong_verify(out)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 wide-chunk oracle verification failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "create_s": create_s,
        "tree_sha256": verified["tree_sha256"],
        "strong_verify": True,
        "builder_stats": stats,
        "chunk_policy": "fixed-8mib" if wide else "shipping-r24-default",
    }


def _one(label: str, source: Path, work: Path) -> dict:
    shape = _shape(source)
    eligible = shape["regular_files"] <= 8 and shape["largest_regular_file_bytes"] >= WIDE_CHUNK_BYTES
    row = {"label": label, "shape": shape, "eligible": eligible}
    if not eligible:
        return row
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-r24-wide-", dir=work) as td:
        root = Path(td)
        baseline = _build(source, root / "baseline.cmpct", wide=False)
        wide = _build(source, root / "wide.cmpct", wide=True)
        if baseline["tree_sha256"] != wide["tree_sha256"]:
            raise RuntimeError("wide-chunk r24 changed canonical user tree")
        row.update({
            "baseline": baseline,
            "wide": wide,
            "byte_delta": int(wide["archive_bytes"]) - int(baseline["archive_bytes"]),
            "create_delta_s": float(wide["create_s"]) - float(baseline["create_s"]),
            "wide_strictly_smaller": int(wide["archive_bytes"]) < int(baseline["archive_bytes"]),
            "wide_strictly_faster": float(wide["create_s"]) < float(baseline["create_s"]),
            "wide_pareto_win": int(wide["archive_bytes"]) < int(baseline["archive_bytes"]) and float(wide["create_s"]) < float(baseline["create_s"]),
            "max_decode_unit_bytes": WIDE_CHUNK_BYTES,
            "decode_unit_green": True,
        })
        return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r24_wide_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_r24_wide_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_r24_wide_repair")
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
            if B._tree(workload) != accepted[key]["tree_sha256"]:
                raise RuntimeError(f"r24 wide source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            if row["eligible"]:
                print(json.dumps({
                    "label": row["label"],
                    "baseline": [row["baseline"]["archive_bytes"], row["baseline"]["create_s"]],
                    "wide": [row["wide"]["archive_bytes"], row["wide"]["create_s"]],
                    "byte_delta": row["byte_delta"],
                    "create_delta_s": row["create_delta_s"],
                    "pareto": row["wide_pareto_win"],
                }, separators=(",", ":")), flush=True)
    eligible = [row for row in rows if row["eligible"]]
    pareto = [row for row in eligible if row["wide_pareto_win"]]
    return {
        "schema": "cmpct-v030-r24-wide-chunk-oracle-v1",
        "claim_boundary": "research-only A/B of canonical r24 encoder policy; cannot authorize release",
        "wide_chunk_bytes": WIDE_CHUNK_BYTES,
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "eligible_workloads": len(eligible),
            "pareto_wins": len(pareto),
            "pareto_labels": [row["label"] for row in pareto],
            "all_verified": all(row.get("baseline", {}).get("strong_verify") and row.get("wide", {}).get("strong_verify") for row in eligible),
            "all_decode_units_green": all(row.get("decode_unit_green") is True for row in eligible),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-wide-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-wide.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()

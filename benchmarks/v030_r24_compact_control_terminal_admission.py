from __future__ import annotations

"""All-15 structural admission proof for terminal C25CC01 selection.

This is deliberately a promotion prerequisite rather than shipping selector code.  The predicate uses only facts
available after the cheap shipping r24 + compact-control candidate exist: logical byte/file counts, r24 expansion
relative to the source tree, and the measured compact-control saving relative to r24.  It never consumes workload
names, paths, suffixes, content hashes, or frozen pack identities.

Every admitted row is then forced through the *complete current product* and same-runner ZIP/Zstd comparators.  A
candidate earns no promotion signal unless it restores the exact tree, is no larger than the complete product, and
is strictly smaller and faster to create than both competitors.  This is intentionally expensive evidence for a
cheap future terminal decision.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT

# These are mechanism-level bounds, not workload identifiers.  The envelope says: compact control may terminalize
# only a non-trivial, effectively incompressible r24 tree when it removes a measurable fraction of control bytes.
MIN_LOGICAL_BYTES = 1 * 1024 * 1024
MIN_REGULAR_FILES = 32
MIN_R24_TO_LOGICAL = 0.98
MAX_CC_TO_R24 = 0.9995
ROUNDS = 3
TARGET_EVIDENCE_ROW = "07_incompressible_and_encrypted_like"


def _source_shape(stage: Path) -> dict:
    sizes = [p.stat().st_size for p in stage.rglob("*") if p.is_file() and not p.is_symlink()]
    return {
        "regular_files": len(sizes),
        "logical_bytes": sum(sizes),
    }


def _admitted(shape: dict, r24_bytes: int, candidate_bytes: int) -> bool:
    logical = int(shape["logical_bytes"])
    return (
        logical >= MIN_LOGICAL_BYTES
        and int(shape["regular_files"]) >= MIN_REGULAR_FILES
        and r24_bytes / max(1, logical) >= MIN_R24_TO_LOGICAL
        and candidate_bytes / max(1, r24_bytes) <= MAX_CC_TO_R24
        and candidate_bytes < r24_bytes
    )


def _build_candidate(stage: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    r24 = root / "shipping-r24.cmpct"
    started = time.perf_counter()
    PRODUCT._locality_bounded_r24_build(stage, r24)
    candidate = root / "candidate.cmpct"
    stats = dict(CC._write_profile(r24, candidate))
    verified = dict(CC.strong_verify(candidate))
    complete = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("C25CC01 candidate strong verification failed")
    return {
        "r24": r24,
        "candidate": candidate,
        "r24_bytes": r24.stat().st_size,
        "candidate_bytes": candidate.stat().st_size,
        "candidate_create_verify_s": complete,
        "candidate_tree": verified["tree_sha256"],
        "payload_unchanged": bool(stats["physical_payload_records_unchanged"]),
        "two_control_copies": bool(stats["two_authenticated_control_copies"]),
    }


def _full_product(stage: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "full-product.cmpct"
    stats = dict(PRODUCT.build(stage, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError("current full product failed strong verification")
    return {
        "bytes": archive.stat().st_size,
        "tree": verified["tree_sha256"],
        "selected": stats.get("selected"),
        "profile": stats.get("format_profile") or stats.get("selected_profile"),
    }


def _competitors(stage: Path, root: Path) -> dict:
    samples = []
    expected = EXT._tree(stage)
    for rep in range(ROUNDS):
        order = ["candidate", "zip", "zstd"]
        order = order[rep % 3 :] + order[: rep % 3]
        row = {}
        for name in order:
            if name == "candidate":
                cand_root = root / f"candidate-{rep}"
                cand_root.mkdir(parents=True, exist_ok=True)
                row[name] = _build_candidate(stage, cand_root)
            elif name == "zip":
                out = root / f"zip-out-{rep}"
                row[name] = EXT._zip(stage, root / f"row-{rep}.zip", out)
                EXT._verify_extracted(out, expected, "zip")
            else:
                out = root / f"zstd-out-{rep}"
                work = root / f"zstd-work-{rep}"
                work.mkdir(parents=True, exist_ok=True)
                row[name] = EXT._tar_zstd(stage, root / f"row-{rep}.tar.zst", out, work)
                EXT._verify_extracted(out, expected, "zstd")
        samples.append(row)

    cb = {int(row["candidate"]["candidate_bytes"]) for row in samples}
    zb = {int(row["zip"]["archive_bytes"]) for row in samples}
    sb = {int(row["zstd"]["archive_bytes"]) for row in samples}
    if len(cb) != 1 or len(zb) != 1 or len(sb) != 1:
        raise RuntimeError("terminal admission comparator bytes were not deterministic")
    cc = statistics.median(float(row["candidate"]["candidate_create_verify_s"]) for row in samples)
    zc = statistics.median(float(row["zip"]["create_s"]) for row in samples)
    sc = statistics.median(float(row["zstd"]["create_s"]) for row in samples)
    candidate_bytes = next(iter(cb))
    zip_bytes = next(iter(zb))
    zstd_bytes = next(iter(sb))
    return {
        "candidate_bytes": candidate_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "median_candidate_create_verify_s": cc,
        "median_zip_create_s": zc,
        "median_zstd19_create_s": sc,
        "strict_four_way_win": candidate_bytes < zip_bytes and candidate_bytes < zstd_bytes and cc < zc and cc < sc,
        "samples": [
            {
                "candidate_s": float(row["candidate"]["candidate_create_verify_s"]),
                "zip_s": float(row["zip"]["create_s"]),
                "zstd19_s": float(row["zstd"]["create_s"]),
            }
            for row in samples
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    sources = CORPUS._build_all(args.work_root / "corpus")
    if len(sources) != 15 or TARGET_EVIDENCE_ROW not in sources:
        raise RuntimeError(f"terminal admission requires exact 15-row corpus; got {len(sources)}")

    rows = []
    for name in sorted(sources):
        row_root = args.work_root / "rows" / name
        row_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-terminal-", dir=row_root) as td:
            root = Path(td)
            stage = EXT._normalized_stage(sources[name], root / "stage-work")
            shape = _source_shape(stage)
            candidate = _build_candidate(stage, root / "candidate-preflight")
            admitted = _admitted(shape, candidate["r24_bytes"], candidate["candidate_bytes"])
            row = {
                "workload": name,
                **shape,
                "r24_bytes": candidate["r24_bytes"],
                "candidate_bytes": candidate["candidate_bytes"],
                "r24_to_logical": candidate["r24_bytes"] / max(1, shape["logical_bytes"]),
                "candidate_to_r24": candidate["candidate_bytes"] / max(1, candidate["r24_bytes"]),
                "admitted": admitted,
                "payload_unchanged": candidate["payload_unchanged"],
                "two_control_copies": candidate["two_control_copies"],
            }
            if admitted:
                full = _full_product(stage, root / "full")
                if full["tree"] != candidate["candidate_tree"]:
                    raise RuntimeError(f"candidate/full-product tree mismatch on {name}")
                competitors = _competitors(stage, root / "competitors")
                row.update({
                    "full_product_bytes": full["bytes"],
                    "candidate_no_larger_than_full_product": candidate["candidate_bytes"] <= full["bytes"],
                    "full_product_selected": full["selected"],
                    "full_product_profile": full["profile"],
                    "competitors": competitors,
                    "strict_four_way_win": competitors["strict_four_way_win"],
                })
            rows.append(row)

    admitted_rows = [row for row in rows if row["admitted"]]
    counterexamples = [
        row["workload"]
        for row in admitted_rows
        if not row.get("candidate_no_larger_than_full_product", False) or not row.get("strict_four_way_win", False)
    ]
    target = next(row for row in rows if row["workload"] == TARGET_EVIDENCE_ROW)
    result = {
        "schema": "cmpct-v030-r24-compact-control-terminal-admission-v1",
        "contract": {
            "predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "min_logical_bytes": MIN_LOGICAL_BYTES,
            "min_regular_files": MIN_REGULAR_FILES,
            "min_r24_to_logical": MIN_R24_TO_LOGICAL,
            "max_candidate_to_r24": MAX_CC_TO_R24,
            "rounds": ROUNDS,
            "release_credit": False,
            "selector_change": False,
        },
        "rows": rows,
        "admitted_count": len(admitted_rows),
        "counterexamples": counterexamples,
        "target_admitted": bool(target["admitted"]),
        "target_four_way_win": bool(target.get("strict_four_way_win", False)),
        "gate": {
            "all15_complete": len(rows) == 15,
            "at_least_one_admitted": bool(admitted_rows),
            "target_admitted": bool(target["admitted"]),
            "zero_counterexamples": not counterexamples,
            "all_admitted_payloads_unchanged": all(row["payload_unchanged"] for row in admitted_rows),
            "all_admitted_two_control_copies": all(row["two_control_copies"] for row in admitted_rows),
            "passed": len(rows) == 15 and bool(admitted_rows) and bool(target["admitted"]) and not counterexamples and all(row["payload_unchanged"] and row["two_control_copies"] for row in admitted_rows),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

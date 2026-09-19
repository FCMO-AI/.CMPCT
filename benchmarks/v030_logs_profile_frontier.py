from __future__ import annotations

"""All-15 shadow frontier for the canonical-filesystem logs inverse profile.

This is a promotion-discovery harness, not release authority.  It asks whether the already bounded/recoverable
logs profile has useful generality beyond the frozen logs workload without changing the shipping selector.
Every credited row must restore the exact frozen regular-file tree.  ZIP/Deflate-9, solid tar+Zstd-19 and the
logs profile are rebuilt three times with rotated execution order; median complete create wall-clock is used so a
millisecond-scale result cannot borrow a fixed warm-cache/order advantage.

A row is a four-way win only when the logs profile is strictly smaller and strictly faster than *both* ZIP and
Zstd.  Equality is failure.  An ineligible/erroring profile is recorded as a fail-closed negative row rather than
aborting the matrix.  This harness cannot authorize selector/native/Android promotion by itself.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS

ROUNDS = 3


def _logs(stage: Path, archive: Path, extracted: Path) -> dict:
    import time

    started = time.perf_counter()
    stats = LOGS.build(stage, archive)
    create_s = time.perf_counter() - started
    verified = LOGS.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"logs profile failed strong verification: {verified!r}")
    started = time.perf_counter()
    LOGS.extract(archive, extracted)
    extract_s = time.perf_counter() - started
    EXT._verify_extracted(extracted, EXT._tree(stage), "logs_inverse_v3")
    return {
        "available": True,
        "archive_bytes": archive.stat().st_size,
        "create_s": create_s,
        "extract_s": extract_s,
        "max_member_read_amplification": stats.get("max_member_read_amplification"),
        "max_decode_unit": stats.get("max_decode_unit"),
        "inverse_edges": stats.get("edge_detection", {}).get("inverse_edges"),
        "inverse_edge_codecs": stats.get("inverse_edge_codecs"),
        "tree_verified": True,
    }


def _measure_round(stage: Path, work: Path, order: tuple[str, ...], round_id: int) -> dict:
    results: dict[str, dict] = {}
    for name in order:
        root = work / f"r{round_id}-{name}"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True)
        try:
            if name == "logs_inverse_v3":
                result = _logs(stage, root / "candidate.cmpct", root / "out")
            elif name == "zip_deflate9":
                result = EXT._zip(stage, root / "archive.zip", root / "out")
                if result.get("available"):
                    EXT._verify_extracted(root / "out", EXT._tree(stage), name)
                    result["tree_verified"] = True
            elif name == "tar_zstd19_solid":
                result = EXT._tar_zstd(stage, root / "archive.tar.zst", root / "out", root)
                if result.get("available"):
                    EXT._verify_extracted(root / "out", EXT._tree(stage), name)
                    result["tree_verified"] = True
            else:
                raise AssertionError(name)
        except Exception as exc:
            result = {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
        results[name] = result
    return results


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-frontier-", dir=work) as td:
        stage = EXT._normalized_stage(source, Path(td))
        names = ("logs_inverse_v3", "zip_deflate9", "tar_zstd19_solid")
        rounds = []
        for round_id in range(ROUNDS):
            shift = round_id % len(names)
            order = names[shift:] + names[:shift]
            rounds.append(_measure_round(stage, Path(td), order, round_id))

        summary = {}
        for name in names:
            measured = [row[name] for row in rounds if row[name].get("available")]
            if len(measured) != ROUNDS:
                reasons = [row[name].get("reason") for row in rounds if not row[name].get("available")]
                summary[name] = {"available": False, "reason": reasons[0] if reasons else "incomplete rounds"}
                continue
            sizes = {int(row["archive_bytes"]) for row in measured}
            if len(sizes) != 1:
                raise RuntimeError(f"non-deterministic archive size for {label}/{name}: {sorted(sizes)}")
            summary[name] = {
                "available": True,
                "archive_bytes": sizes.pop(),
                "median_create_s": statistics.median(float(row["create_s"]) for row in measured),
                "median_extract_s": statistics.median(float(row["extract_s"]) for row in measured),
                "round_create_s": [float(row["create_s"]) for row in measured],
                "tree_verified": all(row.get("tree_verified") is True for row in measured),
            }
            if name == "logs_inverse_v3":
                summary[name].update({
                    "max_member_read_amplification": max(
                        float(row.get("max_member_read_amplification") or 0.0) for row in measured
                    ),
                    "max_decode_unit": max(int(row.get("max_decode_unit") or 0) for row in measured),
                    "inverse_edges": max(int(row.get("inverse_edges") or 0) for row in measured),
                    "inverse_edge_codecs": measured[0].get("inverse_edge_codecs"),
                })

        logs = summary["logs_inverse_v3"]
        zip_row = summary["zip_deflate9"]
        zstd = summary["tar_zstd19_solid"]
        available = all(row.get("available") for row in (logs, zip_row, zstd))
        if available:
            beats_zip_size = int(logs["archive_bytes"]) < int(zip_row["archive_bytes"])
            beats_zstd_size = int(logs["archive_bytes"]) < int(zstd["archive_bytes"])
            beats_zip_create = float(logs["median_create_s"]) < float(zip_row["median_create_s"])
            beats_zstd_create = float(logs["median_create_s"]) < float(zstd["median_create_s"])
        else:
            beats_zip_size = beats_zstd_size = beats_zip_create = beats_zstd_create = False
        four_way = beats_zip_size and beats_zstd_size and beats_zip_create and beats_zstd_create
        return {
            "label": label,
            "formats": summary,
            "strict": {
                "beats_zip_size": beats_zip_size,
                "beats_zstd19_size": beats_zstd_size,
                "beats_zip_create": beats_zip_create,
                "beats_zstd19_create": beats_zstd_create,
                "four_way_win": four_way,
            },
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_logs_frontier_neutral"
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_logs_frontier_hostile"
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_logs_frontier_repair")
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
            expected_tree = accepted[key]["tree_sha256"]
            if EXT._tree(workload) != expected_tree:
                raise RuntimeError(f"source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(json.dumps({"label": row["label"], "strict": row["strict"]}, separators=(",", ":")), flush=True)

    four_way = [row["label"] for row in rows if row["strict"]["four_way_win"]]
    logs_available = [row for row in rows if row["formats"]["logs_inverse_v3"].get("available")]
    locality_green = all(
        float(row["formats"]["logs_inverse_v3"].get("max_member_read_amplification") or 0.0) <= 8.0
        and int(row["formats"]["logs_inverse_v3"].get("max_decode_unit") or 0) <= 8 * 1024 * 1024
        for row in logs_available
    )
    return {
        "schema": "cmpct-v030-logs-profile-frontier-v1",
        "contract": {
            "workloads": 15,
            "rounds": ROUNDS,
            "timing": "median complete create with rotated order",
            "promotion_boundary": "shadow evidence only; no selector/native/Android authority",
            "strict_rule": "logs profile must be strictly smaller and faster than both ZIP/Deflate-9 and solid Zstd-19",
        },
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "profile_available_rows": len(logs_available),
            "four_way_win_count": len(four_way),
            "four_way_win_labels": four_way,
            "all_available_rows_locality_green": locality_green,
        },
        "gate": {
            "exact_workload_count": len(rows) == 15,
            "all_available_rows_tree_verified": all(
                row["formats"]["logs_inverse_v3"].get("tree_verified") is True for row in logs_available
            ),
            "all_available_rows_locality_green": locality_green,
            "logs_workload_four_way": any(
                row["name"] == "05_logs_and_telemetry" and row["strict"]["four_way_win"] for row in rows
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-frontier-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-frontier.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    result["gate"]["passed"] = all(result["gate"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("logs profile shadow frontier failed safety/evidence contract")


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Repeated exact-byte ZIP-factor serial-vs-parallel creation frontier.

This oracle measures the complete candidate creation boundary used by the current ZIP-factor research profile:
source scan + build + publication + cold mandatory strong verification.  ZIP and solid Zstd-19 are rebuilt on the
same runner with rotated execution order.  The parallel candidate receives no performance credit unless its final
archive is byte-for-byte identical to the serial level-3 C25Z3 reference, its verified member identities match an
independent source-filesystem scan, and the canonical source tree remains unchanged.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_parallel_build as PAR

ROUNDS = 9
LEVEL = 3
GROUP_SIZE = 7
WORKERS = 4


def _candidate(stage: Path, archive: Path, *, parallel: bool) -> dict:
    started = time.perf_counter()
    if parallel:
        stats = PAR.build(stage, archive, level=LEVEL, group_size=GROUP_SIZE, workers=WORKERS)
    else:
        stats = V3.build(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verify = V3.verify_and_identities(archive)
    verify_s = time.perf_counter() - started
    return {
        **stats,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "build_s": build_s,
        "verify_s": verify_s,
        "create_s": build_s + verify_s,
        "strong_verify_green": verify["ok"] is True,
        "verified_user_files": verify["verified_user_files"],
        "max_member_read_amplification": verify["max_member_read_amplification"],
        "max_decode_unit_bytes": verify["max_decode_unit_bytes"],
        "identities": {key: [int(value[0]), value[1].hex()] for key, value in verify["identities"].items()},
    }


def _source_identities(stage: Path) -> dict[str, list[object]]:
    """Independent regular-file truth; does not reuse writer/parser state."""
    result: dict[str, list[object]] = {}
    for path in sorted(stage.rglob("*"), key=lambda item: item.relative_to(stage).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        raw = path.read_bytes()
        result[path.relative_to(stage).as_posix()] = [len(raw), hashlib.sha256(raw).hexdigest()]
    return result


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-parallel-", dir=work_root) as raw_td:
        td = Path(raw_td)
        stage = EXT._normalized_stage(source, td)
        truth = CANON._prepare_profile_tree(stage, td / "truth")
        source_tree = CANON._semantic_tree_sha(CANON._decode_manifest(truth["manifest_raw"]))
        source_identities = _source_identities(stage)

        serial_rows: list[dict] = []
        parallel_rows: list[dict] = []
        zip_rows: list[dict] = []
        zstd_rows: list[dict] = []
        order = ["serial", "parallel", "zip", "zstd"]
        for round_index in range(ROUNDS):
            rotated = order[round_index % len(order):] + order[: round_index % len(order)]
            results: dict[str, dict] = {}
            for name in rotated:
                if name == "serial":
                    results[name] = _candidate(stage, td / f"serial-{round_index}.cmpct", parallel=False)
                elif name == "parallel":
                    results[name] = _candidate(stage, td / f"parallel-{round_index}.cmpct", parallel=True)
                elif name == "zip":
                    results[name] = EXT._zip(stage, td / f"base-{round_index}.zip", td / f"zip-out-{round_index}")
                else:
                    results[name] = EXT._tar_zstd(
                        stage,
                        td / f"base-{round_index}.tar.zst",
                        td / f"zstd-out-{round_index}",
                        td / f"zstd-work-{round_index}",
                    )
            serial_rows.append(results["serial"])
            parallel_rows.append(results["parallel"])
            zip_rows.append(results["zip"])
            zstd_rows.append(results["zstd"])

        reference_sha = serial_rows[0]["archive_sha256"]
        reference_bytes = serial_rows[0]["archive_bytes"]
        reference_identities = serial_rows[0]["identities"]
        source_identity_exact = reference_identities == source_identities
        serial_exact = source_identity_exact and all(
            row["archive_sha256"] == reference_sha
            and row["archive_bytes"] == reference_bytes
            and row["identities"] == reference_identities
            and row["strong_verify_green"]
            for row in serial_rows
        )
        parallel_exact = source_identity_exact and all(
            row["archive_sha256"] == reference_sha
            and row["archive_bytes"] == reference_bytes
            and row["identities"] == source_identities
            and row["strong_verify_green"]
            and row["max_member_read_amplification"] <= 8.0
            and row["max_decode_unit_bytes"] <= 8 * 1024 * 1024
            for row in parallel_rows
        )

        serial_create = _median(serial_rows, "create_s")
        parallel_create = _median(parallel_rows, "create_s")
        zip_create = _median(zip_rows, "create_s")
        zstd_create = _median(zstd_rows, "create_s")
        zip_bytes = int(zip_rows[0]["archive_bytes"])
        zstd_bytes = int(zstd_rows[0]["archive_bytes"])
        speedup = (serial_create - parallel_create) / serial_create if serial_create else 0.0

        result = {
            "schema": "cmpct-v030-zipfactor-parallel-build-oracle-v1",
            "claim_boundary": "research scheduling proof only; selector/native/Android/recovery promotion forbidden",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "rounds": ROUNDS,
            "level": LEVEL,
            "group_size": GROUP_SIZE,
            "workers": WORKERS,
            "source_semantic_tree_sha256": source_tree,
            "source_regular_identities": source_identities,
            "serial": {
                "archive_bytes": reference_bytes,
                "archive_sha256": reference_sha,
                "median_create_s": serial_create,
            },
            "parallel": {
                "archive_bytes": reference_bytes,
                "archive_sha256": reference_sha,
                "median_create_s": parallel_create,
                "relative_speedup": speedup,
                "median_build_s": _median(parallel_rows, "build_s"),
                "median_verify_s": _median(parallel_rows, "verify_s"),
            },
            "zip": {"archive_bytes": zip_bytes, "median_create_s": zip_create},
            "tar_zstd19": {"archive_bytes": zstd_bytes, "median_create_s": zstd_create},
        }
        result["gate"] = {
            "serial_exact": serial_exact,
            "parallel_exact_to_serial": parallel_exact,
            "verified_identities_match_independent_source": source_identity_exact,
            "parallel_strictly_faster_than_serial": parallel_create < serial_create,
            "parallel_strictly_smaller_than_zip": reference_bytes < zip_bytes,
            "parallel_strictly_smaller_than_zstd19": reference_bytes < zstd_bytes,
            "parallel_strictly_faster_than_zip": parallel_create < zip_create,
            "parallel_strictly_faster_than_zstd19": parallel_create < zstd_create,
        }
        result["gate"]["passed"] = all(result["gate"].values())
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"serial": result["serial"], "parallel": result["parallel"], "zip": result["zip"], "zstd": result["tar_zstd19"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("parallel ZIP-factor creation oracle did not earn promotion")


if __name__ == "__main__":
    main()

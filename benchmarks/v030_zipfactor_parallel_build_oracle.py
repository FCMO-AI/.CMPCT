from __future__ import annotations

"""Repeated exact-byte ZIP-factor serial-vs-parallel creation frontier.

This oracle measures the complete candidate creation boundary used by the current ZIP-factor research profile:
source scan + build + publication + cold mandatory strong verification. ZIP and solid Zstd-19 are rebuilt on the
same runner with rotated execution order. Parallel scheduling receives no performance credit unless its final
archive is byte-for-byte identical to the serial level-3 C25Z3 reference and independently reconstructed user-file
identities match the source filesystem.

A performance rejection is valid research evidence, not a CI failure. This lane fails only when exactness,
independent source identity, verification, locality, or its own decision accounting is invalid. Release authority
remains elsewhere and still requires the strict per-workload four-way contract.
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
from experiments import entropygraph_v030_product_fs as FS
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
    identities = {key: [int(value[0]), value[1].hex()] for key, value in verify["identities"].items()}
    user_identities = {key: value for key, value in identities.items() if key != FS.FILESYSTEM_MANIFEST}
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
        "identities": identities,
        "user_identities": user_identities,
        "internal_manifest_identity": identities.get(FS.FILESYSTEM_MANIFEST),
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
                    zstd_work = td / f"zstd-work-{round_index}"
                    zstd_work.mkdir(parents=True, exist_ok=True)
                    results[name] = EXT._tar_zstd(
                        stage,
                        td / f"base-{round_index}.tar.zst",
                        td / f"zstd-out-{round_index}",
                        zstd_work,
                    )
            serial_rows.append(results["serial"])
            parallel_rows.append(results["parallel"])
            zip_rows.append(results["zip"])
            zstd_rows.append(results["zstd"])

        reference_sha = serial_rows[0]["archive_sha256"]
        reference_bytes = serial_rows[0]["archive_bytes"]
        reference_user_identities = serial_rows[0]["user_identities"]
        reference_manifest_identity = serial_rows[0]["internal_manifest_identity"]
        source_identity_exact = reference_user_identities == source_identities
        serial_exact = source_identity_exact and all(
            row["archive_sha256"] == reference_sha
            and row["archive_bytes"] == reference_bytes
            and row["user_identities"] == reference_user_identities
            and row["internal_manifest_identity"] == reference_manifest_identity
            and row["strong_verify_green"]
            and row["max_member_read_amplification"] <= 8.0
            and row["max_decode_unit_bytes"] <= 8 * 1024 * 1024
            for row in serial_rows
        )
        parallel_exact = source_identity_exact and all(
            row["archive_sha256"] == reference_sha
            and row["archive_bytes"] == reference_bytes
            and row["user_identities"] == source_identities
            and row["internal_manifest_identity"] == reference_manifest_identity
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
            "schema": "cmpct-v030-zipfactor-parallel-build-oracle-v2",
            "claim_boundary": "research scheduling decision only; selector/native/Android/recovery promotion forbidden",
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
        gate = {
            "serial_exact": serial_exact,
            "parallel_exact_to_serial": parallel_exact,
            "verified_user_identities_match_independent_source": source_identity_exact,
            "parallel_strictly_faster_than_serial": parallel_create < serial_create,
            "parallel_strictly_smaller_than_zip": reference_bytes < zip_bytes,
            "parallel_strictly_smaller_than_zstd19": reference_bytes < zstd_bytes,
            "parallel_strictly_faster_than_zip": parallel_create < zip_create,
            "parallel_strictly_faster_than_zstd19": parallel_create < zstd_create,
        }
        exactness_keys = (
            "serial_exact",
            "parallel_exact_to_serial",
            "verified_user_identities_match_independent_source",
        )
        performance_keys = (
            "parallel_strictly_faster_than_serial",
            "parallel_strictly_smaller_than_zip",
            "parallel_strictly_smaller_than_zstd19",
            "parallel_strictly_faster_than_zip",
            "parallel_strictly_faster_than_zstd19",
        )
        research_evidence_valid = all(gate[key] for key in exactness_keys)
        promotion_earned = research_evidence_valid and all(gate[key] for key in performance_keys)
        result["gate"] = gate
        result["decision"] = {
            "research_evidence_valid": research_evidence_valid,
            "promotion_earned": promotion_earned,
            "verdict": "promote" if promotion_earned else "reject",
            "reason": "bounded parallel scheduling must beat serial and both external creation comparators" if not promotion_earned else "all exactness and performance conditions passed",
        }
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "serial": result["serial"],
        "parallel": result["parallel"],
        "zip": result["zip"],
        "zstd": result["tar_zstd19"],
        "gate": result["gate"],
        "decision": result["decision"],
    }, indent=2), flush=True)
    if not result["decision"]["research_evidence_valid"]:
        raise SystemExit("parallel ZIP-factor research evidence invalid")


if __name__ == "__main__":
    main()

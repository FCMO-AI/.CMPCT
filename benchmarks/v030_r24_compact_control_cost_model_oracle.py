from __future__ import annotations

"""C25CC01 structural cost-model oracle.

The existing terminal predicate correctly finds cases where compact control wins bytes, but unseen high-file-count
mosaics proved that byte eligibility alone does not guarantee a ZIP-speed win.  This oracle does not change the
selector.  It measures the exact phase ownership and cheap structural facts needed to design a safe CPU-aware
admission rule without workload identity.

It compares the frozen encrypted-like target with three independently generated entropy mosaics from the unseen
campaign.  The output deliberately exposes only generic structural/product facts: file count, logical bytes, r24
physical-record/pack shape, source/compact control sizes, compact-control saving, and separately timed r24 build,
profile transform, and mandatory strong verification.  ZIP/Zstd are still measured on the same normalized tree so
agents can identify which phase consumes the available ZIP margin.
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
from benchmarks import v030_r24_compact_control_terminal_admission as ADM
from benchmarks import v030_r24_compact_control_terminal_generalization as GEN
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT

PHASE_ROUNDS = 5
TARGET = "07_incompressible_and_encrypted_like"
MOSAICS = ("entropy_mosaic_640", "entropy_mosaic_1150", "entropy_mosaic_1750")


def _structure(r24: Path) -> dict:
    index, _data, physical = CC._source_r24_parts(r24)
    files = list(index.get("files", []))
    blobs = list(index.get("blobs", []))
    packed = 0
    direct = 0
    for row in files:
        if len(row) <= 6 or row[1] == R24.K_DIR:
            continue
        storage = row[6]
        if storage and storage[0] == R24.S_PACK:
            packed += 1
        else:
            direct += 1
    raw, _compact = CC._compact_raw(index)
    level, comp = CC._compress_control(raw)
    return {
        "semantic_file_rows": len(files),
        "physical_blob_records": len(blobs),
        "s_pack_members": packed,
        "non_pack_members": direct,
        "source_index_raw_bytes": int(physical["index_raw_bytes"]),
        "source_index_comp_bytes_per_copy": int(physical["index_comp_bytes_per_copy"]),
        "physical_data_bytes": int(physical["data_bytes"]),
        "compact_control_raw_bytes": len(raw),
        "compact_control_comp_bytes_per_copy": len(comp),
        "compact_control_level": int(level),
    }


def _phase_round(stage: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    r24 = root / "source-r24.cmpct"
    candidate = root / "candidate.cmpct"

    t0 = time.perf_counter()
    PRODUCT._locality_bounded_r24_build(stage, r24)
    t1 = time.perf_counter()
    structure = _structure(r24)
    t2 = time.perf_counter()
    stats = dict(CC._write_profile(r24, candidate))
    t3 = time.perf_counter()
    verified = dict(CC.strong_verify(candidate))
    t4 = time.perf_counter()
    if not verified.get("ok"):
        raise RuntimeError(f"C25CC01 strong verification failed: {verified!r}")
    return {
        **structure,
        "r24_bytes": r24.stat().st_size,
        "candidate_bytes": candidate.stat().st_size,
        "saving_vs_r24_bytes": r24.stat().st_size - candidate.stat().st_size,
        "r24_build_s": t1 - t0,
        "diagnostic_structure_s": t2 - t1,
        "profile_transform_s": t3 - t2,
        "strong_verify_s": t4 - t3,
        "product_create_verify_s": (t1 - t0) + (t3 - t2) + (t4 - t3),
        "verified_pack_records": int(verified.get("verified_pack_records", 0)),
        "verified_files": int(verified.get("verified_files", 0)),
        "payload_unchanged": bool(stats["physical_payload_records_unchanged"]),
        "two_control_copies": bool(stats["two_authenticated_control_copies"]),
    }


def _measure_case(stage: Path, root: Path) -> dict:
    shape = ADM._source_shape(stage)
    phase_rows = []
    for rep in range(PHASE_ROUNDS):
        phase_rows.append(_phase_round(stage, root / f"phase-{rep}"))
    first = phase_rows[0]
    deterministic_keys = (
        "r24_bytes",
        "candidate_bytes",
        "physical_blob_records",
        "s_pack_members",
        "non_pack_members",
        "source_index_raw_bytes",
        "source_index_comp_bytes_per_copy",
        "physical_data_bytes",
        "compact_control_raw_bytes",
        "compact_control_comp_bytes_per_copy",
        "compact_control_level",
        "verified_pack_records",
        "verified_files",
    )
    for key in deterministic_keys:
        values = {row[key] for row in phase_rows}
        if len(values) != 1:
            raise RuntimeError(f"non-deterministic structural field {key}: {values!r}")

    admitted = ADM._admitted(shape, int(first["r24_bytes"]), int(first["candidate_bytes"]))
    competitors = ADM._competitors(stage, root / "competitors") if admitted else None
    med = lambda key: statistics.median(float(row[key]) for row in phase_rows)
    result = {
        **shape,
        **{key: first[key] for key in deterministic_keys},
        "saving_vs_r24_bytes": int(first["r24_bytes"]) - int(first["candidate_bytes"]),
        "saving_per_regular_file": (int(first["r24_bytes"]) - int(first["candidate_bytes"])) / max(1, int(shape["regular_files"])),
        "r24_to_logical": int(first["r24_bytes"]) / max(1, int(shape["logical_bytes"])),
        "candidate_to_r24": int(first["candidate_bytes"]) / max(1, int(first["r24_bytes"])),
        "packed_member_fraction": int(first["s_pack_members"]) / max(1, int(shape["regular_files"])),
        "files_per_physical_blob": int(shape["regular_files"]) / max(1, int(first["physical_blob_records"])),
        "median_r24_build_s": med("r24_build_s"),
        "median_profile_transform_s": med("profile_transform_s"),
        "median_strong_verify_s": med("strong_verify_s"),
        "median_product_create_verify_s": med("product_create_verify_s"),
        "phase_samples": [
            {
                "r24_build_s": row["r24_build_s"],
                "profile_transform_s": row["profile_transform_s"],
                "strong_verify_s": row["strong_verify_s"],
                "product_create_verify_s": row["product_create_verify_s"],
            }
            for row in phase_rows
        ],
        "admitted_by_current_predicate": admitted,
        "competitors": competitors,
    }
    if competitors is not None:
        zip_s = float(competitors["median_zip_create_s"])
        result["zip_margin_s"] = zip_s - float(result["median_product_create_verify_s"])
        result["phase_fraction_of_zip"] = {
            "r24_build": float(result["median_r24_build_s"]) / max(zip_s, 1e-12),
            "profile_transform": float(result["median_profile_transform_s"]) / max(zip_s, 1e-12),
            "strong_verify": float(result["median_strong_verify_s"]) / max(zip_s, 1e-12),
        }
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    frozen = CORPUS._build_all(args.work_root / "frozen")
    if TARGET not in frozen:
        raise RuntimeError("frozen encrypted-like target missing")
    unseen = GEN._cases(args.work_root / "unseen")
    sources = {"frozen_encrypted_like": frozen[TARGET]}
    sources.update({name: unseen[name] for name in MOSAICS})

    rows = {}
    for name, source in sources.items():
        with tempfile.TemporaryDirectory(prefix=f"cmpct-v030-cc-cost-{name}-", dir=args.work_root) as td:
            root = Path(td)
            stage = EXT._normalized_stage(source, root / "stage")
            rows[name] = _measure_case(stage, root / "measure")

    admitted = [name for name, row in rows.items() if row["admitted_by_current_predicate"]]
    counterexamples = [name for name in admitted if not bool(rows[name]["competitors"]["strict_four_way_win"])]
    result = {
        "schema": "cmpct-v030-c25cc01-structural-cost-model-v1",
        "contract": {
            "selector_change": False,
            "release_credit": False,
            "benchmark_identity_as_policy_input": False,
            "phase_rounds": PHASE_ROUNDS,
            "current_predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "diagnostic_candidate_features": [
                "physical_blob_records",
                "s_pack_members",
                "non_pack_members",
                "source_index_raw_bytes",
                "source_index_comp_bytes_per_copy",
                "compact_control_raw_bytes",
                "compact_control_comp_bytes_per_copy",
                "verified_pack_records",
                "saving_per_regular_file",
                "packed_member_fraction",
                "files_per_physical_blob",
            ],
            "actual_archive_strong_verification_timed": True,
            "diagnostic_structure_scan_excluded_from_product_time": True,
        },
        "rows": rows,
        "admitted_by_current_predicate": admitted,
        "current_predicate_counterexamples": counterexamples,
        "gate": {
            "all_four_cases_complete": len(rows) == 4,
            "frozen_target_admitted": bool(rows["frozen_encrypted_like"]["admitted_by_current_predicate"]),
            "structural_fields_deterministic": True,
            "integrity_preserved": all(row["payload_unchanged"] and row["two_control_copies"] for row in rows.values()),
            "diagnostic_valid": len(rows) == 4 and bool(rows["frozen_encrypted_like"]["admitted_by_current_predicate"]),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

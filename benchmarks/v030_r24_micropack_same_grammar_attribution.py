from __future__ import annotations

"""Same-grammar causal attribution for locality-derived micro-packing.

Mission: docs/V030_R24_MICROPACK_SAME_GRAMMAR_ATTRIBUTION_2026-09-12.md
Research-only. Both physical alternatives pay the exact same membership-v1 grammar.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_hostile_transfer as HOST
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE


def _candidate(source_r24: Path, out: Path, work: Path) -> dict:
    index, data = BASE._parse_r24(source_r24)
    source_verify = BASE.PRODUCT.strong_verify(source_r24)
    if not source_verify.get("ok"):
        raise RuntimeError("source r24 strong verification failed")
    stats = BASE.MEMBERSHIP._write_candidate(source_r24, out)
    verify_dir = work / (out.stem + "-verify")
    verify_dir.mkdir(parents=True, exist_ok=True)
    verified = BASE.MEMBERSHIP._verify_candidate(
        out, index, str(source_verify["tree_sha256"]), verify_dir
    )
    parsed = BASE.MEMBERSHIP._parse_candidate_bytes(out.read_bytes())
    if parsed["index"] != index or parsed["data"] != data:
        raise RuntimeError("same-grammar candidate semantic/payload drift")
    return {
        **stats,
        **verified,
        "archive_bytes": out.stat().st_size,
        "physical_data_bytes": len(data),
        "physical_payload_exact": True,
    }


def _one(source: Path, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)

    independent = work / "independent-r24.cmpct"
    ib = BASE.BUILDER.Builder(source, deflate_reuse_min=0, workers=1)
    ib.micro_pack_max_file = 0
    independent_build = BASE._build_with(ib, independent)
    independent_index, independent_data = BASE._parse_r24(independent)
    independent_verify = BASE.PRODUCT.strong_verify(independent)
    if not independent_verify.get("ok"):
        raise RuntimeError("independent strong verification failed")

    derived = work / "derived-r24.cmpct"
    db = BASE.LocalityDerivedBuilder(source, deflate_reuse_min=0, workers=1)
    db.micro_pack_max_file = BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES
    derived_build = BASE._build_with(db, derived)
    derived_groups = list(getattr(db, "_locality_derived_groups", []))
    derived_index, derived_data = BASE._parse_r24(derived)
    derived_verify = BASE.PRODUCT.strong_verify(derived)
    if not derived_verify.get("ok"):
        raise RuntimeError("derived strong verification failed")
    locality = BASE._pack_locality(derived_index)

    independent_candidate = _candidate(
        independent, work / "independent-membership.cmpct", work
    )
    derived_candidate = _candidate(
        derived, work / "derived-membership.cmpct", work
    )

    same_grammar_delta = int(derived_candidate["archive_bytes"]) - int(independent_candidate["archive_bytes"])
    physical_delta = len(derived_data) - len(independent_data)
    group_count = len(derived_groups)
    group_members = sum(int(g["members"]) for g in derived_groups)

    invariants = {
        "independent_tree_exact": bool(independent_candidate["strong_tree_exact"]),
        "derived_tree_exact": bool(derived_candidate["strong_tree_exact"]),
        "independent_tail_recovery": bool(independent_candidate["primary_corruption_tail_recovery"]),
        "derived_tail_recovery": bool(derived_candidate["primary_corruption_tail_recovery"]),
        "derived_locality_pass": bool(locality["locality_pass"]),
        "independent_payload_exact": bool(independent_candidate["physical_payload_exact"]),
        "derived_payload_exact": bool(derived_candidate["physical_payload_exact"]),
    }

    return {
        "plain_independent_r24_bytes": int(independent_build["archive_bytes"]),
        "plain_derived_r24_bytes": int(derived_build["archive_bytes"]),
        "plain_delta_bytes": int(derived_build["archive_bytes"]) - int(independent_build["archive_bytes"]),
        "same_grammar_independent_bytes": int(independent_candidate["archive_bytes"]),
        "same_grammar_derived_bytes": int(derived_candidate["archive_bytes"]),
        "same_grammar_delta_bytes": same_grammar_delta,
        "independent_physical_data_bytes": len(independent_data),
        "derived_physical_data_bytes": len(derived_data),
        "physical_data_delta_bytes": physical_delta,
        "derived_group_count": group_count,
        "derived_group_members": group_members,
        "max_member_amplification": float(locality["max_member_amplification"]),
        "weighted_member_amplification": float(locality["weighted_member_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "independent_build_cpu_s": float(independent_build["build_cpu_s"]),
        "independent_build_wall_s": float(independent_build["build_wall_s"]),
        "derived_build_cpu_s": float(derived_build["build_cpu_s"]),
        "derived_build_wall_s": float(derived_build["build_wall_s"]),
        "independent_membership_transform_cpu_s": float(independent_candidate["transform_cpu_s"]),
        "independent_membership_transform_wall_s": float(independent_candidate["transform_wall_s"]),
        "derived_membership_transform_cpu_s": float(derived_candidate["transform_cpu_s"]),
        "derived_membership_transform_wall_s": float(derived_candidate["transform_wall_s"]),
        "independent_open_expand_cpu_s": float(independent_candidate["median_open_expand_cpu_s"]),
        "independent_open_expand_wall_s": float(independent_candidate["median_open_expand_wall_s"]),
        "derived_open_expand_cpu_s": float(derived_candidate["median_open_expand_cpu_s"]),
        "derived_open_expand_wall_s": float(derived_candidate["median_open_expand_wall_s"]),
        "invariants": invariants,
        "invariants_pass": all(invariants.values()),
        "economic_pass": (same_grammar_delta < 0) if group_count > 0 else (same_grammar_delta == 0),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    origin_root = work_root / "origin-corpus"
    ATTR._build_sources(origin_root)
    hostile = HOST._build_corpora(work_root / "hostile-corpus")

    sources: dict[str, Path] = {
        "origin_developer": origin_root / "01_developer_repository",
        "origin_tiny_files": origin_root / "08_many_tiny_files",
        **{f"hostile_{name}": path for name, path in hostile.items()},
    }
    rows = {
        name: _one(path, work_root / "work" / name)
        for name, path in sources.items()
    }

    invariant_failures = [name for name, row in rows.items() if not row["invariants_pass"]]
    economic_failures = [name for name, row in rows.items() if not row["economic_pass"]]

    if invariant_failures:
        verdict = "RETIRE_SAME_GRAMMAR_MICROPACK"
    elif economic_failures:
        verdict = "MICROPACK_REQUIRES_EXACT_ECONOMIC_ADMISSION"
    else:
        verdict = "SAME_GRAMMAR_MICROPACK_CAUSAL_WIN"

    return {
        "schema": "cmpct-v030-r24-micropack-same-grammar-attribution-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "locality_budget": BASE.LOCALITY_BUDGET,
        "sources": rows,
        "invariant_failures": invariant_failures,
        "economic_failures": economic_failures,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-micropack-same-grammar-work"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-micropack-same-grammar.json"),
    )
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "invariant_failures": result["invariant_failures"],
        "economic_failures": result["economic_failures"],
        "same_grammar_deltas": {
            name: row["same_grammar_delta_bytes"] for name, row in result["sources"].items()
        },
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

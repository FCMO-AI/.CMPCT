from __future__ import annotations

"""Evidence-bound repair and extension for the C25CC01 structural cost-model oracle.

The v1 oracle measured the required integrity facts in every phase round, but dropped
``payload_unchanged`` and ``two_control_copies`` while collapsing those rounds into the
per-case summary.  This wrapper repairs that boundary and also exposes candidate/logical
overhead signals needed after physical-fragmentation failed to separate a ZIP-speed
counterexample from genuinely fragmented cases.  These are diagnostic candidate facts
only; they do not change selector policy or earn release credit.

A source whose inherited r24 layout is not eligible for C25CC01 under the release locality
law is recorded as negative evidence rather than aborting the four-case diagnostic.  The
row remains non-admitted and cannot earn selector/release credit.
"""

import statistics
from pathlib import Path

from benchmarks import v030_r24_compact_control_cost_model_oracle as BASE


def _measure_case_v2(stage: Path, root: Path) -> dict:
    shape = BASE.ADM._source_shape(stage)
    try:
        phase_rows = [BASE._phase_round(stage, root / f"phase-{rep}") for rep in range(BASE.PHASE_ROUNDS)]
    except BASE.CC.ProfileNotEligible as exc:
        # Preserve the exact r24/source structural facts that caused the rejection.  This is deliberately not a
        # substitute candidate: ineligibility stays red and simply becomes inspectable evidence instead of a crash.
        probe_root = root / "profile-ineligible"
        probe_root.mkdir(parents=True, exist_ok=True)
        r24 = probe_root / "source-r24.cmpct"
        BASE.PRODUCT._locality_bounded_r24_build(stage, r24)
        structure = BASE._structure(r24)
        logical = max(1, int(shape["logical_bytes"]))
        files = max(1, int(shape["regular_files"]))
        return {
            **shape,
            **structure,
            "profile_eligible": False,
            "profile_reject_reason": str(exc),
            "r24_bytes": r24.stat().st_size,
            "candidate_bytes": None,
            "saving_vs_r24_bytes": None,
            "saving_per_regular_file": None,
            "r24_to_logical": r24.stat().st_size / logical,
            "candidate_to_r24": None,
            "candidate_to_logical": None,
            "r24_over_logical_bytes": r24.stat().st_size - logical,
            "candidate_over_logical_bytes": None,
            "candidate_overhead_per_regular_file": None,
            "control_bytes_per_regular_file": None,
            "packed_member_fraction": int(structure["s_pack_members"]) / files,
            "files_per_physical_blob": files / max(1, int(structure["physical_blob_records"])),
            "verified_pack_records": 0,
            "verified_files": 0,
            "payload_unchanged": False,
            "two_control_copies": False,
            "median_r24_build_s": None,
            "median_profile_transform_s": None,
            "median_strong_verify_s": None,
            "median_product_create_verify_s": None,
            "phase_samples": [],
            "admitted_by_current_predicate": False,
            "competitors": None,
        }

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
        "payload_unchanged",
        "two_control_copies",
    )
    for key in deterministic_keys:
        values = {row[key] for row in phase_rows}
        if len(values) != 1:
            raise RuntimeError(f"non-deterministic structural field {key}: {values!r}")

    logical = max(1, int(shape["logical_bytes"]))
    files = max(1, int(shape["regular_files"]))
    r24_bytes = int(first["r24_bytes"])
    candidate_bytes = int(first["candidate_bytes"])
    admitted = BASE.ADM._admitted(shape, r24_bytes, candidate_bytes)
    competitors = BASE.ADM._competitors(stage, root / "competitors") if admitted else None
    med = lambda key: statistics.median(float(row[key]) for row in phase_rows)
    result = {
        **shape,
        **{key: first[key] for key in deterministic_keys},
        "profile_eligible": True,
        "profile_reject_reason": None,
        "saving_vs_r24_bytes": r24_bytes - candidate_bytes,
        "saving_per_regular_file": (r24_bytes - candidate_bytes) / files,
        "r24_to_logical": r24_bytes / logical,
        "candidate_to_r24": candidate_bytes / max(1, r24_bytes),
        "candidate_to_logical": candidate_bytes / logical,
        "r24_over_logical_bytes": r24_bytes - logical,
        "candidate_over_logical_bytes": candidate_bytes - logical,
        "candidate_overhead_per_regular_file": (candidate_bytes - logical) / files,
        "control_bytes_per_regular_file": (2 * int(first["compact_control_comp_bytes_per_copy"])) / files,
        "packed_member_fraction": int(first["s_pack_members"]) / files,
        "files_per_physical_blob": files / max(1, int(first["physical_blob_records"])),
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


BASE._measure_case = _measure_case_v2

if __name__ == "__main__":
    BASE.main()

from __future__ import annotations

"""Complete ZIP-factor frontier with the exact-byte EOCD-indexed source parser.

The isolated parser A/B saves ~0.2 ms while the existing fused-build + in-process-native-verify
frontier trails ZIP by only ~0.15 ms. This composition measures the actual hard timing boundary:
source scan/build, publication and in-process native strong verification versus rotated ZIP and
solid Zstd-19 creation. The candidate parser is allowed into this composition only after the
hostile differential oracle proves it is not more permissive than the mature parser.

Research-only: even a strict four-way signal authorizes canonical parser integration and the
next portability/recovery gates, not release promotion.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_zipfactor_eocd_hostile_equivalence_oracle as HOSTILE
from benchmarks import v030_zipfactor_eocd_indexed_parser_oracle as EOCD
from benchmarks import v030_zipfactor_fused_ffi_complete_frontier as COMPLETE
from experiments import entropygraph_v030_zipfactor_profile as BASE

EXPECTED_BYTES = 14033
EXPECTED_SHA = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"


def run(work_root: Path, library: Path) -> dict:
    hostile = HOSTILE.run()
    if not hostile["gate"]["passed"]:
        raise RuntimeError("EOCD parser hostile-equivalence prerequisite is red")

    old = BASE._parse_zip
    BASE._parse_zip = EOCD._candidate_parse_zip
    try:
        result = COMPLETE.run(work_root, library)
    finally:
        BASE._parse_zip = old

    result["schema"] = "cmpct-v030-zipfactor-eocd-ffi-complete-frontier-v1"
    result["contract"].update(
        {
            "source_parser": "EOCD-indexed-central-first-v1",
            "source_parser_hostile_equivalence_required": True,
            "source_parser_hostile_cases": int(hostile["coverage"]["cases"]),
            "archive_bytes_changed": False,
            "selector_change": False,
            "release_credit": False,
        }
    )
    if int(result["candidate"]["archive_bytes"]) != EXPECTED_BYTES:
        raise RuntimeError("EOCD complete frontier changed candidate byte count")
    if result["candidate"]["archive_sha256"] != EXPECTED_SHA:
        raise RuntimeError("EOCD complete frontier changed candidate SHA-256")
    if not hostile["gate"]["candidate_not_more_permissive"] or not hostile["gate"]["exact_on_shared_acceptance"]:
        raise RuntimeError("EOCD complete frontier lost parser-equivalence prerequisite")

    result["hostile_equivalence"] = {
        "cases": int(hostile["coverage"]["cases"]),
        "candidate_not_more_permissive": True,
        "exact_on_shared_acceptance": True,
    }
    result["release_credit"] = False
    result["promotion_signal"] = bool(result.get("strict_four_way_win", False))
    result["claim_boundary"] = (
        "Research-only complete timing composition. A strict four-way result permits canonical EOCD-parser "
        "productization work only; exact reader/recovery/native/Android/all-15/final authority must be re-earned."
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--native-library", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = run(a.work_root, a.native_library)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sizes": result["sizes"], "medians_s": result["medians_s"], "strict_four_way_win": result["strict_four_way_win"], "hostile_equivalence": result["hostile_equivalence"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("EOCD + FFI complete frontier invalid")


if __name__ == "__main__":
    main()

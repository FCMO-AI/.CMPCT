from __future__ import annotations

"""Complete ZIP-factor frontier with the product-default EOCD-indexed source parser."""

import argparse
import json
from pathlib import Path

from benchmarks import v030_zipfactor_eocd_hostile_equivalence_oracle as HOSTILE
from benchmarks import v030_zipfactor_fused_ffi_complete_frontier as COMPLETE

EXPECTED_BYTES = 14033
EXPECTED_SHA = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"


def run(work_root: Path, library: Path) -> dict:
    hostile = HOSTILE.run()
    if not hostile["gate"]["passed"]:
        raise RuntimeError("EOCD parser hostile-equivalence prerequisite is red")

    # The fused builder now owns parser selection. Do not modify parser globals here: this composition must
    # measure the same ordinary product-side path that downstream recovery/platform gates consume.
    result = COMPLETE.run(work_root, library)
    if result["contract"].get("source_parser") != "EOCD-indexed-central-first-v1":
        raise RuntimeError("complete frontier did not use the product-default EOCD parser")
    if result["contract"].get("source_parser_is_fused_default") is not True:
        raise RuntimeError("complete frontier EOCD parser is not the fused default")

    result["schema"] = "cmpct-v030-zipfactor-eocd-ffi-complete-frontier-v2"
    result["contract"].update(
        {
            "source_parser_hostile_equivalence_required": True,
            "source_parser_hostile_cases": int(hostile["coverage"]["cases"]),
            "process_global_parser_mutation": False,
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
        "Research-only complete timing composition on the product-default EOCD parser. A strict four-way result "
        "advances exact recovery/native/Android/all-15/final authority; it does not unlock release alone."
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
